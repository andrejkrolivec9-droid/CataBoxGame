[app]
title = CataBox
package.name = catabox
package.domain = org.catabox
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,wav,mp3,ogg,ttf,json
version = 1.0

requirements = python3,kivy,pyjnius,android,sqlite3,openssl,certifi

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
