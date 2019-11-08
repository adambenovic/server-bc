import requests

url = r"http://127.0.0.1:5000/diagram/class"
data = {
  "fsPaths": [r"C:\Python27\Lib\site-packages\django\contrib\gis\gdal"],
  "rootPaths": [r"C:\Python27\Lib\site-packages"]
}
print data
response = requests.post(url, json=data)
print response
print response.headers["location"]
