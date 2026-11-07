pip install streamlit requests pandas numpy streamlit-autorefresh scipy
SimuladorNy/
│
├── app.py
├── requirements.txt
├── .streamlit/
│   └── secrets.toml
│
└── assets/
    ├── style.css
    └── app.js
  function changeSport(sport) {
    currentSport = sport;
    selectedLeague = 'Todas';

    document.getElementById('header-icon').textContent =
        sport === 'football' ? '⚽' :
        sport === 'nba' ? '🏀' : '⚾';

    document.getElementById('nav-football')
        .classList.toggle('active', sport === 'football');

    document.getElementById('nav-nba')
        .classList.toggle('active', sport === 'nba');

    document.getElementById('nav-kbo')
        .classList.toggle('active', sport === 'kbo');

    goHome();
    render();
}
