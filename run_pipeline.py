"""Run the full pipeline: ingest -> forecast -> commentary."""
import commentary
import forecast
import ingest

if __name__ == "__main__":
    print("== 1/3 Ingesting EIA data ==")
    ingest.ingest_all()
    print("== 2/3 Fitting ARIMA models ==")
    forecast.run_all()
    print("== 3/3 Generating Groq commentary ==")
    commentary.run_all()
    print("Done. Launch the dashboard with:  streamlit run app.py")
