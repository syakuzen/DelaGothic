from fontTools.ttLib import TTFont, newTable
import glob, shutil, subprocess
import ufo2ft
import ufoLib2
from pathlib import Path
from Foundation import NSURL, NSString, NSConnection
import time, objc
import os
import inspect

# ****************************************************************************************************************************
# Here's where we go through a lot of trouble to export the font out using Glyphs in order to make use of the RoundFont filter.
# Note that this process will take quite *a lot* of time. I don't know of a way to speed this up :(
# ****************************************************************************************************************************

def application(appName):
    port = "com.GeorgSeifert.Glyphs2.JSTalk"
    conn = None
    tries = 0

    while ((conn is None) and (tries < 10)):
        conn = NSConnection.connectionWithRegisteredName_host_(port, None)
        tries = tries + 1;

        if (not conn):
            time.sleep(1)

    if (not conn):
        print("Could not find a JSTalk connection to " + appName)
        return None

    return conn.rootProxy()

Glyphs = application("Glyphs");
GSApplication = Glyphs
if Glyphs and Glyphs.orderedDocuments():
    currentDocument = Glyphs.orderedDocuments()[0]
else:
    currentDocument = None

path = os.path.abspath("Sources/DelaGothic.glyphs")
doc = Glyphs.openDocumentWithContentsOfFile_display_(path, False)
font = doc.font()


for instance in font.instances():
    print ("["+instance.familyName()+"] Exporting")
    url = NSURL.fileURLWithPath_(os.path.abspath("fonts/ttf/%s-%s.ttf" % (str(instance.familyName()).replace(" ",""), instance.name())))
    instance.generate_({
        'ExportFormat':'TTF',
        'Destination':url,
        'autoHint':False,
    })

doc.close()

# *************************************************
# And here's the rest of the 'normal' build process
# *************************************************

exportPath = Path("fonts/ttf")

for file in exportPath.glob("*.ttf"):
    print ("["+str(file).split("/")[2][:-4]+"] adding additional tables and other changes")
    modifiedFont = TTFont(file)
    modifiedFont["DSIG"] = newTable("DSIG")     #need that stub dsig

    modifiedFont["DSIG"].ulVersion = 1
    modifiedFont["DSIG"].usFlag = 0
    modifiedFont["DSIG"].usNumSigs = 0
    modifiedFont["DSIG"].signatureRecords = []
    modifiedFont["head"].flags |= 1 << 3        #sets flag to always round PPEM to integer

    modifiedFont.save(file)

    print ("["+str(file).split("/")[2][:-4]+"] Autohinting")
    subprocess.check_call(
            [
                "ttfautohint",
                "--stem-width",
                "nsn",
                str(file),
                str(file)[:-4]+"-hinted.ttf",
            ]
        )
    shutil.move(str(file)[:-4]+"-hinted.ttf", str(file))