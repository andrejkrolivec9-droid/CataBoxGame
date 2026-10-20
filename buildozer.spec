[app]
title = CataBox
package.name = catabox
package.domain = org.catabox
source.dir = .
source.include_exts = py,png,jpg,jpeg,wav,json,kv
source.exclude_dirs = .github,bin,.buildozer
version = 0.1
requirements = python3,kivy==2.3.0
orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.permissions =

[buildozer]
log_level = 2
warn_on_root = 1
