# ncEllipsisParser
Parse netCDF files as Ellipsis Drive data structures

### Install
```python
pip install ncEllipsisParser
```

### Example
```python
from ncEllipsisParser import parseNetCDF
import ellipsis as el

token = el.account.logIng('your username', 'your password')
parseNetCDF(file ='is path to your file', token=token, epsg = 4326, folderId = None)
