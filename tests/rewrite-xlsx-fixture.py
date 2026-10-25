"""Construct adversarial/desktop-style ZIP metadata for parser regression tests only."""
import io,re,sys
from zipfile import ZipFile,ZIP_DEFLATED
source=ZipFile(io.BytesIO(sys.stdin.buffer.read()));target=io.BytesIO()
with ZipFile(target,'w',ZIP_DEFLATED) as output:
    for name in source.namelist():
        data=source.read(name)
        if name=='xl/worksheets/sheet1.xml' and sys.argv[1]=='dimension':
            data,count=re.subn(rb'<dimension ref="[^"]+"\s*/>',b'<dimension ref="A1"/>',data)
            assert count==1
        if name=='xl/worksheets/sheet1.xml' and sys.argv[1]=='conditional':
            data=data.replace(b'</worksheet>',b'<extLst><ext uri="test" xmlns:xm="http://schemas.microsoft.com/office/excel/2006/main"><xm:f>C2&gt;0</xm:f></ext></extLst></worksheet>')
        output.writestr(name,data)
    if sys.argv[1]=='printer':output.writestr('xl/printerSettings/printerSettings1.bin',b'fictional-printer-metadata')
sys.stdout.buffer.write(target.getvalue())
