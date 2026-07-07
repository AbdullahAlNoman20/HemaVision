<!-- templates/report.html -->
<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HemaVision Report — {{ report_id }}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/vega/5.30.0/vega.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/vega-lite/5.20.1/vega-lite.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/vega-embed/6.26.0/vega-embed.min.js"></script>
</head>
<body>
  <div class="bg-grid"></div>

  <main class="shell print-area">
    <header class="topbar no-print">
      <div class="brand">
        <span class="brand-mark">Hv</span>
        <span class="brand-name">HemaVision</span>
      </div>
      <span class="badge">Report Ready</span>
    </header>

    <section class="report-head">
      <h1>Immunophenotyping Report</h1>
      <div class="meta-row">
        <span class="meta-chip">ID · {{ report_id }}</span>
        <span class="meta-chip">Tubes · 001 &amp; 002</span>
      </div>
    </section>

    <section class="card">
      <h2 class="card-title">Interpretation</h2>
      <p class="interpretation-text">{{ interpretation }}</p>
    </section>

    <section class="card">
      <h2 class="card-title">Marker Chart</h2>
      <div id="markerChart"></div>
    </section>

    <section class="card">
      <h2 class="card-title">Marker Summary</h2>
      <table>
        <thead>
          <tr><th>Tube</th><th>Marker</th><th>Sum Percent</th></tr>
        </thead>
        <tbody>
          {% for row in tables %}
          <tr>
            <td>{{ row["Tube"] }}</td>
            <td>{{ row["Marker"] }}</td>
            <td>{{ "%.2f"|format(row["Sum Percent"]) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>

    <p class="disclaimer">This is an automated screening aid, not a final diagnostic decision. Clinical correlation required.</p>

    <div class="action-row no-print">
      <button onclick="window.print()" class="submit-btn">Print Report</button>
      <a href="{{ url_for('index') }}" class="link-back">← New Upload</a>
    </div>
  </main>

  <script>
    const chartSpec = {{ chart_spec | safe }};
    vegaEmbed('#markerChart', chartSpec, { actions: false, renderer: 'svg' });
  </script>
</body>
</html>