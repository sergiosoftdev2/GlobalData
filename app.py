from flask import Flask, render_template, redirect, request, session
from flask_session import Session
import requests

# URL de la base de datos de Turso y token de autenticación
DB_URL = "https://globaldata-sergiosoftdev2.turso.io/v2/pipeline"
DB_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3MzY3ODU4MDUsImlkIjoiMTJkMDZkNmEtMzgyZi00MjFjLTg2MTktOGQ3NGUxOWY1MjgzIn0.i6sAopB0EsSmHSNKYUFXbLVDkEWeHO8qQX8diboTx0zgYroKkUSAcpY1Ffiu03ZjavmbCIGjWHMNZ4KRiLBEDQ"

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Helper function to make requests to Turso API
def turso_request(query):
    headers = {
        'Authorization': f'Bearer {DB_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "requests": [
            {"type": "execute", "stmt": {"sql": query}},
            {"type": "close"}
        ]
    }
    response = requests.post(DB_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

selectedcountry = ""

@app.route('/', methods=["GET", "POST"])
def hello_world():
    if request.method == "GET":
        return render_template("/index.html")

    elif request.method == "POST":
        inputform = request.form.get("inputform")
        return render_template("/index.html")

@app.route("/trycountries", methods=["GET", "POST"])
def trycountries():
    if request.method == "GET":
        countries = []
        # Hacer consulta a la API de Turso en lugar de usar SQLite
        query = "SELECT short_name FROM wdi_country"
        getcountries = turso_request(query)

        newCountries = getcountries["results"][0]['response']['result']['rows']

        if getcountries:
            for i in newCountries:
                countries.append(i[0]["value"])

        return render_template("/trycountries.html", countries=countries)

    if request.method == "POST":
        selectedcountry = request.form.get("selectedcountry")
        session["country"] = selectedcountry

        # Obtener el CountryCode para el país seleccionado
        query = f"SELECT country_code FROM wdi_country WHERE short_name = '{session['country']}'"
        getcountrycode = turso_request(query)
        session["countrycode"] = getcountrycode['results'][0]['response']['result']["rows"][0][0]["value"]

        return redirect("/tryseries")

@app.route("/tryseries", methods=["POST", "GET"])
def tryseries():
    if request.method == "GET":
        series = []
        # Obtener las series para el país seleccionado
        # Obtener las series para el país seleccionado
        query = f"SELECT a.indicator_name, b.countrycode, b.seriescode " \
                f"FROM wdi_series a INNER JOIN wdi_country_series b ON " \
                f"a.series_code = b.seriescode WHERE b.countrycode = '{session['countrycode']}'"

        
        getseries = turso_request(query)

        getNewSeries = getseries['results'][0]['response']['result']["rows"]

        if getseries:
            for i in getNewSeries:
                series.append(i)

        return render_template("/tryseries.html", series=series,)

    if request.method == "POST":

        gettheseries = request.form['series_data']
        # Obtener los datos de la serie seleccionada
        query = f"SELECT * FROM wdi_Data WHERE country_code = '{session['countrycode']}' AND indicator_code = '{gettheseries}'"
        getdata = turso_request(query)

        if getdata:
            session["data"] = getdata['results'][0]['response']['result']

        return redirect("/results")

@app.route("/results", methods=["GET", "POST"])
def results():
    if request.method == "GET":

        data = session["data"]

        dataDict = {}

        

        for year in data["rows"]:

            newKey = None
            newValue = None

            for floatValue in year:
                if(floatValue["type"] == "integer"):
                    newKey = floatValue["value"]
                if(floatValue["type"] == "float"):
                    newValue = floatValue["value"]

            if year is not None and newValue is not None:
                dataDict[newKey] = newValue     




        datakeys = list(dataDict.keys())[4:]
        datavalues = list(dataDict.values())[4:]

        return render_template("/results.html", data=data, datakeys=datakeys, datavalues=datavalues)

if __name__ == '__main__':
    app.run(debug=True)
