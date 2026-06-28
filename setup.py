from setuptools import setup


APP = ["run_app.py"]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "assets/tianxiawuzei.icns",
    "plist": {
        "CFBundleName": "天下无贼",
        "CFBundleDisplayName": "天下无贼",
        "CFBundleIdentifier": "com.shijian.tianxiawuzei",
        "CFBundleShortVersionString": "0.3.0",
        "CFBundleVersion": "0.3.0",
        "LSUIElement": True,
        "NSHumanReadableCopyright": "Free to use; no warranty.",
    },
    "packages": ["rumps", "tianxiawuzei"],
}


setup(
    app=APP,
    name="天下无贼",
    options={"py2app": OPTIONS},
)
