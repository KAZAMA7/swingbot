"""
NIFTY 500 Symbols for Yahoo Finance

Complete list of NIFTY 500 stocks with Yahoo Finance symbol format (.NS suffix)
"""

# NIFTY 500 symbols - Yahoo Finance format (with .NS suffix for NSE stocks)
NIFTY_500_SYMBOLS = [
    # Large Cap Stocks
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
    "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS",
    "ASIANPAINT.NS", "LT.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS", "NESTLEIND.NS", "POWERGRID.NS",
    "NTPC.NS", "HCLTECH.NS", "BAJFINANCE.NS", "M&M.NS", "TECHM.NS",
    "TATAMOTORS.NS", "COALINDIA.NS", "TATASTEEL.NS", "ADANIPORTS.NS", "ONGC.NS",
    "INDUSINDBK.NS", "JSWSTEEL.NS", "GRASIM.NS", "HINDALCO.NS", "CIPLA.NS",
    "DRREDDY.NS", "EICHERMOT.NS", "UPL.NS", "APOLLOHOSP.NS", "BAJAJFINSV.NS",
    "DIVISLAB.NS", "HDFCLIFE.NS", "SBILIFE.NS", "BRITANNIA.NS", "SHREECEM.NS",
    "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "GODREJCP.NS", "PIDILITIND.NS", "DABUR.NS",
    
    # Mid Cap Stocks
    "ADANIGREEN.NS", "ADANIENT.NS", "ADANITRANS.NS", "AUROPHARMA.NS", "BANKBARODA.NS",
    "BERGEPAINT.NS", "BIOCON.NS", "BOSCHLTD.NS", "BPCL.NS", "CADILAHC.NS",
    "CANBK.NS", "CHOLAFIN.NS", "COLPAL.NS", "CONCOR.NS", "CUMMINSIND.NS",
    "DLF.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GAIL.NS",
    "GODREJPROP.NS", "HAVELLS.NS", "HDFC.NS", "HDFCAMC.NS", "IBULHSGFIN.NS",
    "ICICIPRULI.NS", "IDEA.NS", "IDFCFIRSTB.NS", "INDIGO.NS", "IOC.NS",
    "IRCTC.NS", "JINDALSTEL.NS", "JUBLFOOD.NS", "L&TFH.NS", "LICHSGFIN.NS",
    "LUPIN.NS", "MARICO.NS", "MCDOWELL-N.NS", "MFSL.NS", "MOTHERSUMI.NS",
    "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NMDC.NS", "NAUKRI.NS",
    "OBEROIRLTY.NS", "OFSS.NS", "PAGEIND.NS", "PETRONET.NS", "PFC.NS",
    "PIIND.NS", "PNB.NS", "POLYCAB.NS", "PVR.NS", "RAMCOCEM.NS",
    "RECLTD.NS", "SAIL.NS", "SIEMENS.NS", "SRF.NS", "TORNTPHARM.NS",
    "TRENT.NS", "TVSMOTOR.NS", "VEDL.NS", "VOLTAS.NS", "ZEEL.NS",
    
    # Small Cap and Others
    "3MINDIA.NS", "AAVAS.NS", "ABB.NS", "ABCAPITAL.NS", "ABFRL.NS",
    "ACC.NS", "ADANIPOWER.NS", "AEGISCHEM.NS", "AFFLE.NS", "AJANTPHARM.NS",
    "AKZOINDIA.NS", "ALKEM.NS", "AMARAJABAT.NS", "AMBUJACEM.NS", "APOLLOTYRE.NS",
    "ASHOKLEY.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AVANTI.NS",
    "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BATAINDIA.NS", "BEL.NS",
    "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BLISSGVS.NS",
    "BLUEDART.NS", "BSOFT.NS", "CANFINHOME.NS", "CAPLIPOINT.NS", "CARBORUNIV.NS",
    "CASTROLIND.NS", "CCL.NS", "CEATLTD.NS", "CENTURYTEX.NS", "CERA.NS",
    "CHAMBLFERT.NS", "CHENNPETRO.NS", "CHOLAHLDNG.NS", "CLEAN.NS", "COFORGE.NS",
    "COROMANDEL.NS", "CROMPTON.NS", "CUB.NS", "CUMMINSIND.NS", "CYIENT.NS",
    "DEEPAKNTR.NS", "DELTACORP.NS", "DHANUKA.NS", "DIXON.NS", "DMART.NS",
    "DRREDDY.NS", "EIDPARRY.NS", "EIHOTEL.NS", "EMAMILTD.NS", "ENDURANCE.NS",
    "ENGINERSIN.NS", "EQUITAS.NS", "ERIS.NS", "ESABINDIA.NS", "FINEORG.NS",
    "FINCABLES.NS", "FLUOROCHEM.NS", "FORTIS.NS", "FSL.NS", "GICRE.NS",
    "GILLETTE.NS", "GLAXO.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS",
    "GODFRYPHLP.NS", "GRANULES.NS", "GRAPHITE.NS", "GREAVESCOT.NS", "GRINDWELL.NS",
    "GSFC.NS", "GSPL.NS", "GUJALKALI.NS", "GUJGASLTD.NS", "HAL.NS",
    "HAPPSTMNDS.NS", "HATSUN.NS", "HCC.NS", "HEG.NS", "HEIDELBERG.NS",
    "HEXAWARE.NS", "HFCL.NS", "HIMATSEIDE.NS", "HINDZINC.NS", "HONAUT.NS",
    "HUDCO.NS", "IBREALEST.NS", "ICICIBANK.NS", "IDBI.NS", "IDFC.NS",
    "IFBIND.NS", "IIFL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS",
    "INDIANB.NS", "INDOCO.NS", "INDUSINDBK.NS", "INFIBEAM.NS", "INOXLEISUR.NS",
    "INTELLECT.NS", "IOB.NS", "IPCALAB.NS", "IRB.NS", "ISEC.NS",
    "ITDC.NS", "ITI.NS", "JBCHEPHARM.NS", "JCHAC.NS", "JETAIRWAYS.NS",
    "JKCEMENT.NS", "JKLAKSHMI.NS", "JKPAPER.NS", "JMFINANCIL.NS", "JSL.NS",
    "JSWENERGY.NS", "JUSTDIAL.NS", "JYOTHYLAB.NS", "KAJARIACER.NS", "KANSAINER.NS",
    "KEI.NS", "KNRCON.NS", "KRBL.NS", "L&TFH.NS", "LALPATHLAB.NS",
    "LAURUSLABS.NS", "LAXMIMACH.NS", "LEMONTREE.NS", "LINDEINDIA.NS", "LTI.NS",
    "LTTS.NS", "LUXIND.NS", "LXCHEM.NS", "MANAPPURAM.NS", "MASFIN.NS",
    "MAXHEALTH.NS", "MCDOWELL-N.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS",
    "MINDACORP.NS", "MINDTREE.NS", "MIDHANI.NS", "MOIL.NS", "MOTILALOFS.NS",
    "MPHASIS.NS", "MRPL.NS", "MUTHOOTFIN.NS", "NATCOPHARM.NS", "NATIONALUM.NS",
    "NAUKRI.NS", "NAVINFLUOR.NS", "NBCC.NS", "NCC.NS", "NESTLEIND.NS",
    "NETWORK18.NS", "NHPC.NS", "NIITLTD.NS", "NLCINDIA.NS", "NOCIL.NS",
    "NRBBEARING.NS", "NTPC.NS", "NUCLEUS.NS", "OBEROIRLTY.NS", "OIL.NS",
    "OMAXE.NS", "ONGC.NS", "ORIENTBANK.NS", "PAGEIND.NS", "PARAGMILK.NS",
    "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PFIZER.NS", "PGHH.NS",
    "PHOENIXLTD.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "PNBHOUSING.NS",
    "POLYCAB.NS", "POLYMED.NS", "POWERGRID.NS", "PRSMJOHNSN.NS", "PTC.NS",
    "PVR.NS", "QUESS.NS", "RADICO.NS", "RAIN.NS", "RAJESHEXPO.NS",
    "RALLIS.NS", "RAMCOCEM.NS", "RBLBANK.NS", "RECLTD.NS", "REDINGTON.NS",
    "RELAXO.NS", "RELCAPITAL.NS", "RELIANCE.NS", "RELINFRA.NS", "RNAM.NS",
    "ROUTE.NS", "RPOWER.NS", "RSYSTEMS.NS", "RTNINDIA.NS", "SAIL.NS",
    "SANOFI.NS", "SBICARD.NS", "SBILIFE.NS", "SCHAEFFLER.NS", "SCHNEIDER.NS",
    "SCI.NS", "SFL.NS", "SHANKARA.NS", "SHILPAMED.NS", "SHOPERSTOP.NS",
    "SHREECEM.NS", "SHRIRAMFIN.NS", "SIEMENS.NS", "SIS.NS", "SJVN.NS",
    "SKFINDIA.NS", "SOBHA.NS", "SOLARINDS.NS", "SONATSOFTW.NS", "SOUTHBANK.NS",
    "SPANDANA.NS", "SPARC.NS", "SPICEJET.NS", "SRTRANSFIN.NS", "SRF.NS",
    "STARCEMENT.NS", "STLTECH.NS", "SUDARSCHEM.NS", "SUNDARMFIN.NS", "SUNDRMFAST.NS",
    "SUNPHARMA.NS", "SUNTV.NS", "SUPRAJIT.NS", "SUPREMEIND.NS", "SUVEN.NS",
    "SWANENERGY.NS", "SYMPHONY.NS", "SYNDIBANK.NS", "SYNGENE.NS", "TAKE.NS",
    "TATACHEM.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAELXSI.NS", "TATAMOTORS.NS",
    "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TEAMLEASE.NS", "TECHM.NS",
    "THERMAX.NS", "THOMASCOOK.NS", "THYROCARE.NS", "TIFHL.NS", "TIMKEN.NS",
    "TITAN.NS", "TORNTPHARM.NS", "TORNTPOWER.NS", "TRENT.NS", "TRIDENT.NS",
    "TRITURBINE.NS", "TTKPRESTIG.NS", "TV18BRDCST.NS", "TVSMOTOR.NS", "UBL.NS",
    "UJJIVAN.NS", "ULTRACEMCO.NS", "UNIONBANK.NS", "UPL.NS", "UTTAMSUGAR.NS",
    "VAIBHAVGBL.NS", "VARROC.NS", "VBL.NS", "VEDL.NS", "VENKEYS.NS",
    "VGUARD.NS", "VINATIORGA.NS", "VIPIND.NS", "VOLTAS.NS", "VTL.NS",
    "WABAG.NS", "WELCORP.NS", "WELSPUNIND.NS", "WESTLIFE.NS", "WHIRLPOOL.NS",
    "WIPRO.NS", "WOCKPHARMA.NS", "YESBANK.NS", "ZEEL.NS", "ZENSARTECH.NS",
    "ZYDUSWELL.NS"
]

# Top 50 NIFTY stocks for testing (most liquid and reliable)
NIFTY_50_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
    "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS",
    "ASIANPAINT.NS", "LT.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS", "NESTLEIND.NS", "POWERGRID.NS",
    "NTPC.NS", "HCLTECH.NS", "BAJFINANCE.NS", "M&M.NS", "TECHM.NS",
    "TATAMOTORS.NS", "COALINDIA.NS", "TATASTEEL.NS", "ADANIPORTS.NS", "ONGC.NS",
    "INDUSINDBK.NS", "JSWSTEEL.NS", "GRASIM.NS", "HINDALCO.NS", "CIPLA.NS",
    "DRREDDY.NS", "EICHERMOT.NS", "UPL.NS", "APOLLOHOSP.NS", "BAJAJFINSV.NS",
    "DIVISLAB.NS", "HDFCLIFE.NS", "SBILIFE.NS", "BRITANNIA.NS", "SHREECEM.NS",
    "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "GODREJCP.NS", "PIDILITIND.NS", "DABUR.NS"
]

# Top 100 NIFTY stocks for medium testing
NIFTY_100_SYMBOLS = NIFTY_50_SYMBOLS + [
    "ADANIGREEN.NS", "ADANIENT.NS", "ADANITRANS.NS", "AUROPHARMA.NS", "BANKBARODA.NS",
    "BERGEPAINT.NS", "BIOCON.NS", "BOSCHLTD.NS", "BPCL.NS", "CADILAHC.NS",
    "CANBK.NS", "CHOLAFIN.NS", "COLPAL.NS", "CONCOR.NS", "CUMMINSIND.NS",
    "DLF.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "GAIL.NS",
    "GODREJPROP.NS", "HAVELLS.NS", "HDFC.NS", "HDFCAMC.NS", "IBULHSGFIN.NS",
    "ICICIPRULI.NS", "IDEA.NS", "IDFCFIRSTB.NS", "INDIGO.NS", "IOC.NS",
    "IRCTC.NS", "JINDALSTEL.NS", "JUBLFOOD.NS", "L&TFH.NS", "LICHSGFIN.NS",
    "LUPIN.NS", "MARICO.NS", "MCDOWELL-N.NS", "MFSL.NS", "MOTHERSUMI.NS",
    "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NMDC.NS", "NAUKRI.NS",
    "OBEROIRLTY.NS", "OFSS.NS", "PAGEIND.NS", "PETRONET.NS", "PFC.NS"
]

def get_symbol_list(size="nifty50"):
    """
    Get symbol list based on size preference.
    
    Args:
        size: "nifty50", "nifty100", or "nifty500"
        
    Returns:
        List of symbols
    """
    if size.lower() == "nifty50":
        return NIFTY_500_SYMBOLS[:50]  # First 50 symbols (large cap)
    elif size.lower() == "nifty100":
        return NIFTY_500_SYMBOLS[:100]  # First 100 symbols
    elif size.lower() == "nifty500":
        return NIFTY_500_SYMBOLS  # All 500 symbols
    else:
        return NIFTY_500_SYMBOLS[:50]  # Default to NIFTY 50

def validate_symbols(symbols, max_test=5):
    """
    Validate a subset of symbols to ensure they work with Yahoo Finance.
    
    Args:
        symbols: List of symbols to validate
        max_test: Maximum number of symbols to test
        
    Returns:
        Dictionary with validation results
    """
    import yfinance as yf
    
    test_symbols = symbols[:max_test]
    results = {
        'tested': len(test_symbols),
        'valid': 0,
        'invalid': 0,
        'details': {}
    }
    
    for symbol in test_symbols:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="5d")
            
            if not data.empty:
                results['valid'] += 1
                results['details'][symbol] = {
                    'status': 'valid',
                    'records': len(data),
                    'latest_price': float(data['Close'].iloc[-1])
                }
            else:
                results['invalid'] += 1
                results['details'][symbol] = {'status': 'no_data'}
                
        except Exception as e:
            results['invalid'] += 1
            results['details'][symbol] = {'status': 'error', 'error': str(e)}
    
    return results

if __name__ == "__main__":
    print("NIFTY Symbols for Yahoo Finance")
    print("=" * 40)
    print(f"NIFTY 50: {len(NIFTY_50_SYMBOLS)} symbols")
    print(f"NIFTY 100: {len(NIFTY_100_SYMBOLS)} symbols") 
    print(f"NIFTY 500: {len(NIFTY_500_SYMBOLS)} symbols")
    
    print("\nValidating sample symbols...")
    results = validate_symbols(NIFTY_50_SYMBOLS, 5)
    
    print(f"Tested: {results['tested']}")
    print(f"Valid: {results['valid']}")
    print(f"Invalid: {results['invalid']}")
    
    for symbol, details in results['details'].items():
        if details['status'] == 'valid':
            print(f"✅ {symbol}: Rs.{details['latest_price']:.2f}")
        else:
            print(f"❌ {symbol}: {details['status']}")