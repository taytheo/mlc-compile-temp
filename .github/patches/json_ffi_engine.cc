#include "json_ffi_engine.h"

#include <picojson.h>
#include <tvm/ffi/function.h>
#include <tvm/ffi/reflection/registry.h>
#include <tvm/runtime/module.h>

#include <filesystem>
#include <fstream>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <string>

// Optional bridge to iOS shim - no-op on platforms that don't provide
// mlc_emit_diagnostic. We declare as C symbol so a platform-specific
// implementation (e.g. mlc_shim.mm) can forward diagnostics to Flutter.
extern "C" void mlc_emit_diagnostic(const char* json_str);

#include "../serve/model.h"
#include "../support/json_parser.h"
#include "../support/result.h"

namespace mlc {
namespace llm {
namespace json_ffi {

using namespace tvm::runtime;

// Forward declare EmitPersistentHostDiag so constructor can call it before
// the function is defined later in this translation unit.
static void EmitPersistentHostDiag(const std::string &json_str);

JSONFFIEngine::JSONFFIEngine() {
  engine_ = serve::ThreadedEngine::Create();
  try {
    EmitPersistentHostDiag(std::string("{""type"":""jsonffi_init"",""message"":""engine_created""}"));
  } catch (...) {}
}

// Write a small persistent diagnostic to /tmp and to stderr using POSIX
// APIs so it will be visible in host-side captures even when higher-level
// logging paths are missed. Keep this function tiny and failure-tolerant.
static void EmitPersistentHostDiag(const std::string &json_str) {
  // Mirror to stderr (best-effort)
  try {
    std::string line = std::string("[JSONFFI-HOST] ") + json_str + "\n";
    // Use low-level write to avoid stdio buffering surprises in some runtimes
    ssize_t wn = write(STDERR_FILENO, line.data(), line.size());
    (void)wn;
  } catch (...) {}

  // Append to a file in /tmp so the runner can always fetch it
  try {
    const char *path = "/tmp/mlc_jsonffi_diagnostics.log";
    int fd = open(path, O_CREAT | O_WRONLY | O_APPEND, 0644);
    if (fd >= 0) {
      std::string line = json_str + "\n";
      ssize_t wn = write(fd, line.data(), line.size());
      (void)wn;
      // best-effort flush
      fsync(fd);
      close(fd);
    }
  } catch (...) {}
}

bool JSONFFIEngine::ChatCompletion(std::string request_json_str, std::string request_id) {
  bool success = this->AddRequest(request_json_str, request_id);
  if (!success) {
    this->StreamBackError(request_id);
  }
  return success;
}

void JSONFFIEngine::StreamBackError(std::string request_id) {
  ChatCompletionMessage delta;
  delta.content = this->err_;
  delta.role = "assistant";

  ChatCompletionStreamResponseChoice choice;
  choice.finish_reason = FinishReason::error;
  choice.index = 0;
  choice.delta = delta;

  ChatCompletionStreamResponse response;
  response.id = request_id;
  response.choices = std::vector<ChatCompletionStreamResponseChoice>{choice};
  response.model = "json_ffi";  // TODO: Return model name from engine (or from args)
  response.system_fingerprint = "";

  picojson::array response_arr;
  response_arr.push_back(picojson::value(response.AsJSON()));

  // now stream back the final usage block, which is required.
  // NOTE: always stream back final usage block as it is an
  // invariant of the system
  response.choices.clear();
  picojson::object dummy_usage;
  dummy_usage["prompt_tokens"] = picojson::value(static_cast<int64_t>(0));
  dummy_usage["completion_tokens"] = picojson::value(static_cast<int64_t>(0));
  dummy_usage["total_tokens"] = picojson::value(static_cast<int64_t>(0));
  response.usage = picojson::value(dummy_usage);
  response_arr.push_back(picojson::value(response.AsJSON()));

  std::string stream_back_json = picojson::value(response_arr).serialize();
  this->request_stream_callback_(stream_back_json);
}

bool JSONFFIEngine::AddRequest(std::string request_json_str, std::string request_id) {
  Result<ChatCompletionRequest> request_res = ChatCompletionRequest::FromJSON(request_json_str);
  if (request_res.IsErr()) {
    err_ = request_res.UnwrapErr();
    return false;
  }
  ChatCompletionRequest request = request_res.Unwrap();
  Array<Data> inputs;
  Array<String> stop_strs;
  bool is_special_request =
      (request.debug_config.has_value() &&
       request.debug_config.value().special_request != SpecialRequestKind::kNone);
  // special request does not have to go through prompt construction
  if (!is_special_request) {
    // get prompt: note, assistant was appended in the end.
    Result<std::vector<Data>> inputs_obj =
        CreatePrompt(this->conv_template_, request, this->model_config_, this->device_);
    if (inputs_obj.IsErr()) {
      err_ = inputs_obj.UnwrapErr();
      return false;
    }
    inputs = inputs_obj.Unwrap();

    stop_strs.reserve(this->conv_template_.stop_str.size());
    for (const std::string& stop_str : this->conv_template_.stop_str) {
      stop_strs.push_back(stop_str);
    }
    if (request.stop.has_value()) {
      stop_strs.reserve(stop_strs.size() + request.stop.value().size());
      for (const std::string& stop_str : request.stop.value()) {
        stop_strs.push_back(stop_str);
      }
    }
  }
  // create a generation config from request
  const auto& default_gen_cfg = default_generation_config_;
  auto gen_cfg = tvm::ffi::make_object<GenerationConfigNode>();
  gen_cfg->n = request.n;
  gen_cfg->temperature = request.temperature.value_or(default_gen_cfg->temperature);
  gen_cfg->top_p = request.top_p.value_or(default_gen_cfg->top_p);
  gen_cfg->frequency_penalty =
      request.frequency_penalty.value_or(default_gen_cfg->frequency_penalty);
  gen_cfg->presence_penalty = request.presence_penalty.value_or(default_gen_cfg->presence_penalty);
  gen_cfg->logprobs = request.logprobs;
  gen_cfg->top_logprobs = request.top_logprobs;
  gen_cfg->logit_bias = request.logit_bias.value_or(default_gen_cfg->logit_bias);
  gen_cfg->seed = request.seed.value_or(std::random_device{}());
  gen_cfg->max_tokens = request.max_tokens.value_or(default_gen_cfg->max_tokens);
  gen_cfg->stop_strs = std::move(stop_strs);
  gen_cfg->stop_token_ids = conv_template_.stop_token_ids;
  gen_cfg->response_format = request.response_format.value_or(ResponseFormat());
  gen_cfg->debug_config = request.debug_config.value_or(DebugConfig());

  Result<GenerationConfig> res_gen_config = GenerationConfig::Validate(GenerationConfig(gen_cfg));
  if (res_gen_config.IsErr()) {
    err_ = res_gen_config.UnwrapErr();
    return false;
  }

  Request engine_request(request_id, inputs, res_gen_config.Unwrap());

  // setup request state
  RequestState rstate;
  rstate.model = request.model.value_or("");
  rstate.streamer.reserve(gen_cfg->n);
  for (int i = 0; i < gen_cfg->n; ++i) {
    rstate.streamer.push_back(TextStreamer(tokenizer_));
  }
  // Avoid copy-assign requirement and be compatible with headers that may
  // not expose atomic counters: move available members and leave defaults
  {
    auto &dst = request_map_[request_id];
    dst.model = std::move(rstate.model);
    dst.streamer = std::move(rstate.streamer);
  }

  this->engine_->AddRequest(engine_request);
  return true;
}

bool JSONFFIEngine::Abort(std::string request_id) {
  this->engine_->AbortRequest(request_id);
  auto it = request_map_.find(request_id);
  if (it != request_map_.end()) {
    request_map_.erase(it);
  }
  return true;
}

std::string JSONFFIEngine::GetLastError() { return err_; }

void JSONFFIEngine::ExitBackgroundLoop() { this->engine_->ExitBackgroundLoop(); }

JSONFFIEngine::~JSONFFIEngine() { this->ExitBackgroundLoop(); }

class JSONFFIEngineImpl : public JSONFFIEngine, public ffi::ModuleObj {
 public:
  TVM_MODULE_VTABLE_BEGIN("mlc.json_ffi");
  TVM_MODULE_VTABLE_ENTRY("init_background_engine", &JSONFFIEngineImpl::InitBackgroundEngine);
  TVM_MODULE_VTABLE_ENTRY("reload", &JSONFFIEngineImpl::Reload);
  TVM_MODULE_VTABLE_ENTRY("unload", &JSONFFIEngineImpl::Unload);
  TVM_MODULE_VTABLE_ENTRY("reset", &JSONFFIEngineImpl::Reset);
  TVM_MODULE_VTABLE_ENTRY("chat_completion", &JSONFFIEngineImpl::ChatCompletion);
  TVM_MODULE_VTABLE_ENTRY("abort", &JSONFFIEngineImpl::Abort);
  TVM_MODULE_VTABLE_ENTRY("get_last_error", &JSONFFIEngineImpl::GetLastError);
  TVM_MODULE_VTABLE_ENTRY("run_background_loop", &JSONFFIEngineImpl::RunBackgroundLoop);
  TVM_MODULE_VTABLE_ENTRY("run_background_stream_back_loop",
                          &JSONFFIEngineImpl::RunBackgroundStreamBackLoop);
  TVM_MODULE_VTABLE_ENTRY("exit_background_loop", &JSONFFIEngineImpl::ExitBackgroundLoop);
  TVM_MODULE_VTABLE_END();

  void InitBackgroundEngine(int device_type, int device_id,
                            Optional<Function> request_stream_callback) {
    DLDevice device{static_cast<DLDeviceType>(device_type), device_id};
    this->device_ = device;
    CHECK(request_stream_callback.defined())
        << "JSONFFIEngine requires request stream callback function, but it is not given.";
    this->request_stream_callback_ = request_stream_callback.value();

    auto frequest_stream_callback_wrapper = [this](ffi::PackedArgs args, ffi::Any* ret) {
      ICHECK_EQ(args.size(), 1);
      Array<RequestStreamOutput> delta_outputs = args[0].cast<Array<RequestStreamOutput>>();
      std::string responses = this->GetResponseFromStreamOutput(delta_outputs);
      this->request_stream_callback_(responses);
    };

    request_stream_callback = Function(frequest_stream_callback_wrapper);
    this->engine_->InitThreadedEngine(device, std::move(request_stream_callback), std::nullopt);
  }

  void Reload(String engine_config_json_str) {
    try {
      this->engine_->Reload(engine_config_json_str);
      this->default_generation_config_ = this->engine_->GetDefaultGenerationConfig();
      auto engine_config = this->engine_->GetCompleteEngineConfig();

        // Debug: print which model path we're loading so we can correlate on-device
        // runtime behavior with the packaged model path (helps determine whether
        // the model config being loaded matches the files in the app bundle).
        fprintf(stderr, "[JSONFFI] Reload: engine_config.model='%s'\n",
              engine_config->model.c_str());
        // Inject a guaranteed EventChannel diagnostic via the shim helper so
        // we can detect JSONFFI engine reloads in device logs even when other
        // diagnostic sinks are not captured by the runner.
        try {
          std::ostringstream _diag;
          _diag << "{""type"":""jsonffi_reload"",""model"":""" << engine_config->model << """}";
          mlc_emit_diagnostic(_diag.str().c_str());
          extern "C" void mlc_emit_diag_to_token(const char* json_str);
          mlc_emit_diag_to_token(_diag.str().c_str());
        } catch (...) {}

        // Also emit a diagnostic listing files present under the model path so we
        // can quickly detect missing shard files or incorrect paths when running
        // on-device (helps rule out asset packaging problems).
        try {
          std::filesystem::path model_path(engine_config->model);
          picojson::array files_json;
          if (std::filesystem::exists(model_path)) {
            if (std::filesystem::is_directory(model_path)) {
              for (auto &p : std::filesystem::directory_iterator(model_path)) {
                files_json.push_back(picojson::value(std::string(p.path().filename())));
              }
            } else {
              files_json.push_back(picojson::value(model_path.filename().string()));
            }
          } else {
            files_json.push_back(picojson::value(std::string("(missing)")));
          }
          picojson::object model_files_diag;
          model_files_diag["type"] = picojson::value(std::string("model_files_listing"));
          model_files_diag["modelPath"] = picojson::value(engine_config->model);
          model_files_diag["files"] = picojson::value(files_json);
          std::string model_files_diag_str = picojson::value(model_files_diag).serialize();
          mlc_emit_diagnostic(model_files_diag_str.c_str());
          // Persist a copy for host-side debugging and correlation
          EmitPersistentHostDiag(model_files_diag_str);
        } catch (...) {
          // ignore any errors during diagnostics emission
        }

        // Load conversation template.
    Result<picojson::object> model_config_json =
        serve::Model::LoadModelConfig(engine_config->model);
    CHECK(model_config_json.IsOk()) << model_config_json.UnwrapErr();
    const picojson::object& model_config_json_unwrapped = model_config_json.Unwrap();
    Result<Conversation> conv_template = Conversation::FromJSON(
        json::Lookup<picojson::object>(model_config_json_unwrapped, "conv_template"));
    CHECK(!conv_template.IsErr()) << "Invalid conversation template JSON: "
                                  << conv_template.UnwrapErr();
    this->conv_template_ = conv_template.Unwrap();
    // Debug: print conv_template.roles contents to help diagnose "user" role problems
    try {
      std::ostringstream _ss_roles;
      _ss_roles << "[JSONFFI] conv_template.roles size=" << this->conv_template_.roles.size()
                << " keys=";
      bool _first = true;
      picojson::array role_keys;
      for (const auto &kv : this->conv_template_.roles) {
        if (!_first) _ss_roles << ',';
        _ss_roles << kv.first;
        _first = false;
        role_keys.push_back(picojson::value(kv.first));
      }
      fprintf(stderr, "%s\n", _ss_roles.str().c_str());

      // Try to emit an EventChannel-friendly diagnostic via the platform shim
      try {
        picojson::object diag;
        diag["type"] = picojson::value(std::string("jsonffi_diag"));
        diag["modelPath"] = picojson::value(engine_config->model);
            for (size_t i = 0; i < delta_output->group_finish_reason.size(); ++i) {
        // Indicate that additional token id prefix diagnostics are compiled
        // into this build (helps confirm the current binary includes the
        // patch enabling jsonffi_token_ids_prefix emissions).
        diag["token_ids_prefix_enabled"] = picojson::value(true);
        std::string diag_str = picojson::value(diag).serialize();
        // safe-call: mlc_emit_diagnostic might not be present on all platforms
        mlc_emit_diagnostic(diag_str.c_str());
      ... (file continues)
