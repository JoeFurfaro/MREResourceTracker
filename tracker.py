from re import M
import pyodbc
import json
import os

from datetime import date, timedelta

def loadTracker(includedResources):

    pwd = os.environ.get('CMSPASS')
    if not pwd:
        raise Exception("ENV VARIABLE CMS PASS IS NOT SET")
    conn = pyodbc.connect(f"DSN=CMSDAT;UID=JOEFURFARO;PWD={pwd};SYSTEM=s10138ag;DBQ=CMSDAT CMSDAT;DFTPKGLIB=QGPL;LANGUAGEID=ENU;PKG=QGPL/DEFAULT(IBM),2,0,1,0,512;QRYSTGLMT=-1;")

    cursor = conn.cursor()

    start = date.today() - timedelta(days=2)
    end = date.today() + timedelta(days=25)

    def exec(cursor, query):
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results

    customerPartsFile = open("customer_parts.txt", "r")
    customer_parts = [x.strip() for x in customerPartsFile.readlines()]
    customerPartsFile.close()

    commonPartsFile = open("common_parts.txt", "r")
    common_parts = [x.strip() for x in commonPartsFile.readlines()]
    commonPartsFile.close()

    common_parts = dict(zip(customer_parts, common_parts))

    qohReady = exec(cursor, "SELECT STKB.BXPART, STKB.BXQTOH, STKB.BXUNIT, STKB.BXSTOK FROM S6506D0B.CMSDAT.STKB STKB WHERE (STKB.BXQTOH Not In (0)) AND (STKB.BXPLNT='DFT') AND (STKB.BXSTOK Not In ('DFTQ25','DFTXXX'))")

    qoh = {}
    for part in qohReady:
        qoh[part["BXPART"].strip()] = sum([x["BXQTOH"] for x in qohReady if x["BXPART"] == part["BXPART"]])

    commonGood = {}
    commonTotalGood = {}
    for partNum in common_parts:
        try:
            commonGood[partNum.strip()] = qoh[partNum.strip()]
        except:
            continue

    for part in commonGood:
        commonTotalGood[part] = sum([commonGood[x] for x in commonGood if common_parts[x] == common_parts[part]])

    results = exec(cursor, f"SELECT SSCH.JYCODE, SSCH.JYDATE, SSCH.JYTIME, SSCH.JYENTR, SSCH.JYODAT, SSCH.JYOTME, SSCH.JYSQTY, SSCH.JYBSUN, SSCH.JYORUN, SSCH.JYOWCD, SSCH.JYAPPR, SSCH.JYORWS, SSCH.JYORDR, SSCH.JYITEM, SSCH.JYRELN, SSCH.JYAUTH, SSCH.JYPORL, SSCH.JYPART, SSCH.JYSCUS, SSCH.JYSTKL, SSCH.JYTERR, SSCH.JYCUMQ, SSCH.JYCUMY, SSCH.JYDOCK, SSCH.JYSEQN, SSCH.JYRANY, SSCH.JYRAN, SSCH.JYKANB, SSCH.JYINTC, SSCH.JYLATF, SSCH.JYPLNT, SSCH.JYJITK, SSCH.JYFUT1, SSCH.JYFUT2, SSCH.JYFUT3, SSCH.JYFUT4, SSCH.JYFUT5, SSCH.JYFUT6, SSCH.JYFUT7, SSCH.JYFUT8, SSCH.JYFLG1, SSCH.JYFLG2, SSCH.JYFLG3, SSCH.JYLSDT, SSCH.JYLSTI, SSCH.JYLSTZ, SSCH.JYLODT, SSCH.JYLOTI, SSCH.JYLOTZ, SSCH.JYTRPTI, SSCH.JYTRPTM FROM S6506D0B.CMSDAT.SSCH SSCH\
        WHERE (SSCH.JYDATE>='{start}' AND SSCH.JYDATE<='{end}') ORDER BY SSCH.JYPART, SSCH.JYDATE ASC")

    pMasterM = exec(cursor, "SELECT STKMM.AVPART, STKMM.AVDES1 FROM S6506D0B.CMSDAT.STKMM STKMM")
    pMasterP = exec(cursor, "SELECT STKMP.AWPART, STKMP.AWDES1 FROM S6506D0B.CMSDAT.STKMP STKMP WHERE (STKMP.AWDPLT='DFT')")

    routing = exec(cursor, f"SELECT METHDR.AOPART, METHDR.AODEPT, METHDR.AORESC, METHDR.AOSEQ#, METHDR.AORUNS, METHDR.AOUNIT, METHDR.AORTYP, METHDR.AO#MEN, METHDR.AO#MCH, METHDR.AOSETP FROM S6506D0B.CMSDAT.METHDR METHDR")
    resources = {}
    des1 = {}
    des2 = {}

    for route in routing:
        resources["DFT" + route["AOPART"]] = route["AORESC"]
    for part in pMasterM:
        des1[part["AVPART"]] = part["AVDES1"]
    for part in pMasterP:
        des2[part["AWPART"]] = part["AWDES1"]

    for i,result in enumerate(results):
        # Resources
        try:
            result["Resource"] = resources["DFT" + result["JYPART"]]
        except:
            result["Resource"] = None
        try:
            result["QOH"] = commonTotalGood[result["JYPART"].strip()]
            resultSamePart = i != 0 and results[i]["JYPART"].strip() == results[i-1]["JYPART"].strip()
            result["CUM"] = result["QOH"] - result["JYSQTY"] if not resultSamePart else results[i-1]["CUM"] - result["JYSQTY"]
        except:
            result["QOH"] = None
            result["CUM"] = None

        try:
            result["Description"] = des1[result["JYPART"]]
        except:
            try:
                result["Description"] = des2[result["JYPART"]]
            except:
                result["Description"] = None

        # Part #    
        result["Part #"] = result["JYPART"].strip()

    results = [r for r in results if r["Resource"] != None and r["Resource"].strip() in includedResources]

    allParts = list(set([x["JYPART"].strip() for x in results]))

    data = []

    allDates = set()

    for part in allParts:
        cur = {}
        quants = []
        dates = set([str(x["JYDATE"]) for x in results if x["Part #"] == part])
        for d in sorted(dates):
            allDates.add(d)
            qohs = [x["CUM"] for x in results if x["Part #"] == part and str(x["JYDATE"]) == d and x["CUM"] != None]
            minQOH = None if len(qohs) == 0 else min(qohs)
            if minQOH is None:
                continue
            quants.append({
                "Date": str(d),
                "MinQOH": float(minQOH) if minQOH is not None else None 
            })
        first = [x for x in results if x["Part #"] == part][0]
        cur["PartNo"] = first["Part #"]
        cur["Quants"] = quants
        if len(quants) == 0:
            continue
        cur["Description"] = first["Description"].strip()
        cur["QOH"] = float(first["QOH"]) if first["QOH"] is not None else None 
        cur["Resource"] = first["Resource"].strip()
        data.append(cur)

    for part in data:
        dates = [q["Date"] for q in part["Quants"]]
        for d in allDates:
            if d not in dates:
                part["Quants"].append({"Date": d, "MinQOH": None})
        part["Quants"] = sorted(part["Quants"], key=(lambda quant: quant["Date"]))

    conn.close()

    return data