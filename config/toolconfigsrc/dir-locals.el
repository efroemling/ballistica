;; -*- lexical-binding: t; -*-

(

 ;; Stuff that applies everywhere.
 (nil . (
         ;; Short project name to save some space in mode-lines/messages/etc.
         (project-vc-name . "bainternal")

         ;; Extra paths that searches and whatnot should ignore. Note that
         ;; gitignored stuff is ignored implicitly.
         ;; IMPORTANT - seems dirs need trailing slashes here.
         (project-vc-ignores . ("submodules/"
                                "src/external/"
                                "ballisticakit-android/BallisticaKit/src/main/cpp/src" ;; a symlink - no trailing slash
                                "src/assets/ba_data/python-site-packages/"
                                "src/assets/pylib-android/"
                                "src/assets/pylib-apple/"
                                "src/assets/windows/"
                                "tools/make_bob/"
                                "tools/mali_texture_compression_tool/"
                                "tools/nvidia_texture_tools/"
                                "tools/powervr_tools/"
                                "*.wav"
                                "*.png"
                                "*.obj"
                                ))))
 
 __EFRO_EMACS_STANDARD_CPP_LSP_SETUP__

 __EFRO_EMACS_STANDARD_PYTHON_LSP_SETUP__
 
 )
