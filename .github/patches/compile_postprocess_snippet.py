# .github/patches/compile_postprocess_snippet.py
# Append iOS built static libs to the generated model tar (best-effort).
try:
    from pathlib import Path
    import tarfile, subprocess, logging

    # This snippet expects `args` object (present in compile.py scope)
    if "iphone" in str(args.target):
        mlc_root = Path(__file__).resolve().parents[2]
        ios_prepare = mlc_root / "ios" / "prepare_libs.sh"
        if ios_prepare.exists():
            logging.info("Invoking ios/prepare_libs.sh to build iOS static libs")
            subprocess.run(["bash", str(ios_prepare)], check=True, cwd=str(mlc_root))
            built_lib_dir = mlc_root / "build" / "lib"
            if built_lib_dir.exists():
                try:
                    with tarfile.open(args.output, mode="a") as tarf:
                        for lib in sorted(built_lib_dir.iterdir()):
                            if lib.is_file():
                                arcname = f"lib/{lib.name}"
                                logging.info("Adding %s to %s as %s", lib, args.output, arcname)
                                tarf.add(str(lib), arcname=arcname)
                    logging.info("Appended iOS static libs to %s", str(args.output))
                except Exception as e:
                    logging.warning("Failed to append built iOS libs to tar: %s", e)
        else:
            logging.info("ios/prepare_libs.sh not found; skipping iOS lib inclusion")
except Exception as e:
    # Non-fatal: best-effort
    import logging
    logging.warning("Post-process iOS lib inclusion failed: %s", e)
