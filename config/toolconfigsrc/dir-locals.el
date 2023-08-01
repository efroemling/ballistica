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
 
 ;; Set up clangd as our C++ language server.
 (c++-ts-mode . ((eglot-server-programs . ((c++-ts-mode . ("clangd" "--compile-commands-dir=.cache/compile_commands_db"))))))

 ;; Set up python-lsp-server as our Python language server.
 (python-ts-mode . (
     (eglot-server-programs . (
         (python-ts-mode . ("__EFRO_PY_BIN__" "-m" "pylsp"))))
     (python-shell-interpreter . "__EFRO_PY_BIN__")
     (eglot-workspace-configuration . (
         (:pylsp . (:plugins (
             :pylint (:enabled t)
             :flake8 (:enabled :json-false)
             :pycodestyle (:enabled :json-false)
             :mccabe (:enabled :json-false)
             :autopep8 (:enabled :json-false)
             :pyflakes (:enabled :json-false)
             :rope_autoimport (:enabled :json-false)
             :rope_completion (:enabled :json-false)
             :rope_rename (:enabled :json-false)
             :yapf (:enabled :json-false)
             :black (:enabled t
                     :skip_string_normalization t
                     :line_length 80
                     :cache_config t)
             :jedi (:extra_paths [__EFRO_PYTHON_PATHS_Q_REL_STR__])
             :pylsp_mypy (:enabled t
                          :live_mode nil
                          :dmypy t))))))))
 )
