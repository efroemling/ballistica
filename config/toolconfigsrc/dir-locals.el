;; -*- lexical-binding: t; -*-

(

 ;; Stuff that applies everywhere.
 (nil . (
         ;; Short project name to save some space in mode-lines/messages/etc.
         (project-vc-name . "bainternal")

         ;; Extra paths that searches and whatnot should ignore. Note that
         ;; gitignored stuff is ignored implicitly.
         (project-vc-ignores . ("docs"
                                "submodules"
                                "src/external"
                                "src/assets/ba_data/python-site-packages"
                                "src/assets/pylib-android"
                                "src/assets/pylib-apple"
                                "src/assets/windows"))))
 
 __EFRO_EMACS_STANDARD_CPP_LSP_SETUP__

 __EFRO_EMACS_STANDARD_PYTHON_LSP_SETUP__
 
 )
