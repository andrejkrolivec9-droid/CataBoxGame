[app]

title = CataBox
package.name = catabox
package.domain = org.catabox

source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,kv,atlas,ttf,otf,wav,mp3,ogg,json,db,txt

icon.filename = %(source.dir)s/CataBox_icon-2.png

version = 4.5.0
android.numeric_version = 45000

requirements = python3,kivy,pyjnius,android,requests,urllib3,chardet,certifi,idna,six,setuptools

orientation = portrait
fullscreen = 1

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
