# Location Lifestyle AI v1.0

Fresh Streamlit repository. Upload all files and folders to a new GitHub repository, preserving the directory structure. Deploy `app.py` in Streamlit Community Cloud.

## Included
- Flexible UK location matching
- Lifestyle priorities and household profile
- Lifestyle fingerprint
- 0–3, 3–8 and 8–15 year assessment
- Stay Active, Curious Mind, Community, Family, Outdoors, Blue-space and Practicality sections
- Approximate family/work/care journey comparison
- Optional user-supplied listing sample
- Optional PropertyData and OpenTripMap connectors via Streamlit Secrets
- Downloadable HTML report
- Source-health panel

## Optional secrets
Copy values from `.streamlit/secrets.toml.example` into Streamlit Community Cloud Secrets. Never commit live keys to GitHub.

## Property CSV
Use `data/sample_listings.csv` as the template. Required columns: `area`, `price`. Optional: `property_type`, `bedrooms`, `url`.
