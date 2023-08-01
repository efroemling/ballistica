;; -*- lexical-binding: t; -*-

(
 
 ;; Specify some extra paths that project.el searches and whatnot should ignore.
 ;; Note that gitignored stuff is ignored implicitly.
 (nil . ((project-vc-ignores . ("docs"
                                "submodules"
                                "src/external"
                                "src/assets/ba_data/python-site-packages"
                                "src/assets/pylib-android"
                                "src/assets/pylib-apple"
                                "src/assets/windows"))))
 
 __EFRO_EMACS_STANDARD_CPP_LSP_SETUP__

 __EFRO_EMACS_STANDARD_PYTHON_LSP_SETUP__
 
 )
