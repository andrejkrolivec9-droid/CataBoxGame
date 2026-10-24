[app]

title = CataBox
package.name = catabox
package.domain = org.catabox

source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,kv,atlas,ttf,otf,wav,mp3,ogg,json,db,txt

icon.filename = %(source.dir)s/CataBox_icon.png

version = 4.0.8
android.numeric_version = 40800

requirements = python3,hostpython3,kivy,pyjnius,android,requests,urllib3,chardet,certifi,idna,sqlite3,six,setuptools,libffi,openssl,sdl2_image,sdl2_mixer,sdl2_ttf

orientation = portrait
fullscreen = 0

android.permissions = INTERNET

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.release_artifact = apk
android.debug_artifact = apk

p4a.branch = v2024.01.21

[buildozer]

log_level = 2
warn_on_root = 1
