import streamlit as st

st.set_page_config(page_title="SimuladorNy", page_icon="🏀", layout="centered")

html_code = """
<!DOCTYPE html>
<html lang="es" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>SimuladorNy — Inteligencia Cuantitativa</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        darkBg: '#0b0d10',
                        cardBg: '#12151c',
                        cardHover: '#1a1f2c',
                        borderSubtle: '#222733',
                        textMuted: '#9ca3af',
                        textLight: '#f3f4f6'
                    },
                    fontFamily: {
                        sans: ['Plus Jakarta Sans', 'Inter', 'sans-serif']
                    }
                }
            }
        }
    </script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            background-color: #0b0d10;
            color: #f3f4f6;
            font-family: 'Plus Jakarta Sans', sans-serif;
            -webkit-tap-highlight-color: transparent;
        }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #0b0d10; }
        ::-webkit-scrollbar-thumb { background: #222733; border-radius: 4px; }
        .glass-panel {
            background: rgba(18, 21, 28, 0.85);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .match-card {
            background: rgba(18, 21, 28, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: all 0.2s ease;
        }
        .match-card:hover {
            background: rgba(26, 31, 44, 0.9);
            border-color: rgba(255, 255, 255, 0.12);
        }
        .sport-pill {
            background: rgba(25, 30, 40, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.2s ease;
        }
        .sport-pill.active {
            background: #ffffff;
            color: #0b0d10;
            border-color: #ffffff;
        }
        @keyframes pulseLive {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.95); }
        }
        .live-dot {
            animation: pulseLive 1.5s ease-in-out infinite;
        }
    </style>
</head>
<body class="min-h-screen pb-32 selection:bg-neutral-800 selection:text-white">

    <header class="sticky top-0 z-50 glass-panel border-b border-borderSubtle px-4 py-3">
        <div class="max-w-md mx-auto flex items-center justify-between">
            <div class="flex items-center space-x-2.5 cursor-pointer" onclick="app.goHome()">
                <div class="w-8 h-8 rounded-xl bg-neutral-900 border border-neutral-700 flex items-center justify-center text-sm shadow-inner">
                    🏀
                </div>
                <div>
                    <h1 class="font-extrabold text-sm tracking-wider text-white uppercase leading-tight">Simulador<span class="text-neutral-400">Ny</span></h1>
                    <p class="text-[8px] text-textMuted uppercase tracking-widest font-bold">Analysis AI</p>
                </div>
            </div>
            <div class="flex items-center space-x-2">
                <span class="text-[10px] px-2.5 py-1 rounded-full bg-neutral-900 border border-neutral-800 text-textMuted font-bold">Modelos Activos</span>
            </div>
        </div>
    </header>

    <main class="max-w-md mx-auto px-4 pt-4">
        <div class="relative mb-4">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-neutral-500 text-xs">🔍</span>
            <input type="text" id="search-input" oninput="app.setSearch(this.value)" placeholder="Buscar equipos o ligas..." 
                class="w-full bg-cardBg border border-borderSubtle text-textLight text-xs rounded-xl pl-9 pr-4 py-2.5 focus:outline-none focus:border-neutral-500 placeholder-neutral-500 shadow-md">
        </div>

        <div id="app-content"></div>
    </main>

    <nav class="fixed bottom-0 left-0 right-0 z-50 bg-[#0b0d10]/95 backdrop-blur-xl border-t border-borderSubtle px-3 py-3">
        <div class="max-w-md mx-auto grid grid-cols-5 gap-1.5 text-center">
            <button onclick="app.setSport('futbol')" id="pill-futbol" class="sport-pill py-2 rounded-xl flex flex-col items-center justify-center space-y-1 text-neutral-400">
                <span class="text-base">⚽</span>
                <span class="text-[9px] uppercase font-bold tracking-wider">Fútbol</span>
            </button>
            <button onclick="app.setSport('nhl')" id="pill-nhl" class="sport-pill py-2 rounded-xl flex flex-col items-center justify-center space-y-1 text-neutral-400">
                <span class="text-base">🏒</span>
                <span class="text-[9px] uppercase font-bold tracking-wider">NHL</span>
            </button>
            <button onclick="app.setSport('nba')" id="pill-nba" class="sport-pill active py-2 rounded-xl flex flex-col items-center justify-center space-y-1">
                <span class="text-base">🏀</span>
                <span class="text-[9px] uppercase font-bold tracking-wider">NBA</span>
            </button>
            <button onclick="app.setSport('nfl')" id="pill-nfl" class="sport-pill py-2 rounded-xl flex flex-col items-center justify-center space-y-1 text-neutral-400">
                <span class="text-base">🏈</span>
                <span class="text-[9px] uppercase font-bold tracking-wider">NFL</span>
            </button>
            <button onclick="app.setSport('mlb')" id="pill-mlb" class="sport-pill py-2 rounded-xl flex flex-col items-center justify-center space-y-1 text-neutral-400">
                <span class="text-base">⚾</span>
                <span class="text-[9px] uppercase font-bold tracking-wider">MLB</span>
            </button>
        </div>
    </nav>

    <script>
        const teamBadges = {
            "Nuggets": "https://a.espncdn.com/i/teamlogos/nba/500/den.png",
            "Pacers": "https://a.espncdn.com/i/teamlogos/nba/500/ind.png",
            "Nets": "https://a.espncdn.com/i/teamlogos/nba/500/bkn.png",
            "Hawks": "https://a.espncdn.com/i/teamlogos/nba/500/atl.png",
            "Knicks": "https://a.espncdn.com/i/teamlogos/nba/500/ny.png",
            "Cavaliers": "https://a.espncdn.com/i/teamlogos/nba/500/cle.png",
            "Wizards": "https://a.espncdn.com/i/teamlogos/nba/500/wsh.png",
            "Thunder": "https://a.espncdn.com/i/teamlogos/nba/500/okc.png",
            "Magic": "https://a.espncdn.com/i/teamlogos/nba/500/orl.png",
            "Warriors": "https://a.espncdn.com/i/teamlogos/nba/500/gs.png",
            "Rockets": "https://a.espncdn.com/i/teamlogos/nba/500/hou.png",
            "Suns": "https://a.espncdn.com/i/teamlogos/nba/500/phx.png",
            "Spurs": "https://a.espncdn.com/i/teamlogos/nba/500/sas.png",
            "Trail Blazers": "https://a.espncdn.com/i/teamlogos/nba/500/por.png"
        };

        const sportsData = {
            "nba": {
                "🇺🇸 NBA, Estados Unidos": {
                    "Nuggets vs Pacers": { local: "Nuggets", visitante: "Pacers", estado: "EN VIVO", marcador: "64 - 41", periodo: "HT", base_l: 114.5, base_v: 104.0, is_nba: true },
                    "Nets vs Hawks": { local: "Nets", visitante: "Hawks", hora: "5:30 p.m.", base_l: 108.0, base_v: 112.5, is_nba: true },
                    "Knicks vs Cavaliers": { local: "Knicks", visitante: "Cavaliers", hora: "6:00 p.m.", base_l: 110.0, base_v: 113.0, is_nba: true },
                    "Wizards vs Thunder": { local: "Wizards", visitante: "Thunder", hora: "6:00 p.m.", base_l: 105.5, base_v: 119.0, is_nba: true },
                    "Magic vs Warriors": { local: "Magic", visitante: "Warriors", hora: "6:30 p.m.", base_l: 107.0, base_v: 112.0, is_nba: true },
                    "Rockets vs Suns": { local: "Rockets", visitante: "Suns", hora: "7:00 p.m.", base_l: 111.0, base_v: 114.5, is_nba: true },
                    "Spurs vs Trail Blazers": { local: "Spurs", visitante: "Trail Blazers", hora: "8:00 p.m.", base_l: 109.0, base_v: 107.5, is_nba: true }
                }
            },
            "futbol": {
                "🇲🇽 Mexico · Liga MX": {
                    "Atlas vs Pachuca": { local: "Atlas", visitante: "Pachuca", estado: "EN VIVO", marcador: "1 - 1", periodo: "2T 78'", base_l: 1.15, base_v: 1.40, metric1_lbl: "Tarjetas amarillas", metric1_val: "5", metric2_lbl: "Córners", metric2_val: "10.6" }
                }
            }
        };

        class SimuladorApp {
            constructor() {
                this.currentSport = 'nba';
                this.currentView = 'list';
                this.selectedLeague = null;
                this.selectedMatch = null;
                this.searchQuery = '';
                this.init();
            }

            init() { this.render(); }

            goHome() {
                this.selectedLeague = null;
                this.selectedMatch = null;
                this.currentView = 'list';
                this.render();
            }

            setSport(sport) {
                this.currentSport = sport;
                ['futbol', 'nhl', 'nba', 'nfl', 'mlb'].forEach(s => {
                    const el = document.getElementById(`pill-${s}`);
                    if(el) {
                        if(s === sport) el.className = "sport-pill active py-2 rounded-xl flex flex-col items-center justify-center space-y-1";
                        else el.className = "sport-pill py-2 rounded-xl flex flex-col items-center justify-center space-y-1 text-neutral-400";
                    }
                });
                this.goHome();
            }

            setSearch(val) {
                this.searchQuery = val.toLowerCase();
                this.render();
            }

            openDetail(liga, partidoKey) {
                this.selectedLeague = liga;
                this.selectedMatch = partidoKey;
                this.currentView = 'detail';
                this.render();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }

            runSimulation(m) {
                if(m.is_nba) {
                    let simL = Math.round(m.base_l + (Math.random() * 6 - 3));
                    let simV = Math.round(m.base_v + (Math.random() * 6 - 3));
                    if(simL === simV) simL += 2;
                    let totalPts = simL + simV;
                    let probL = simL > simV ? 58 : 42;
                    let probV = 100 - probL;
                    return {
                        ptsL: simL,
                        ptsV: simV,
                        totalPts: totalPts,
                        ganador: simL > simV ? m.local : m.visitante,
                        probL: probL,
                        probV: probV
                    };
                } else {
                    return { ganador: m.local, probL: 50, probV: 50 };
                }
            }

            render() {
                const container = document.getElementById('app-content');
                const leagueData = sportsData[this.currentSport];

                if(this.currentView === 'detail') {
                    const m = sportsData[this.currentSport][this.selectedLeague][this.selectedMatch];
                    const badgeL = teamBadges[m.local] || 'https://a.espncdn.com/i/teamlogos/soccer/500/default.png';
                    const badgeV = teamBadges[m.visitante] || 'https://a.espncdn.com/i/teamlogos/soccer/500/default.png';
                    const sim = this.runSimulation(m);

                    container.innerHTML = `
                        <button onclick="app.goHome()" class="mb-4 text-xs font-semibold px-3 py-1.5 rounded-xl bg-cardBg border border-borderSubtle text-textLight">← Volver</button>
                        <div class="glass-panel rounded-2xl p-5 mb-4 text-center">
                            <p class="text-[9px] text-textMuted uppercase tracking-widest font-bold mb-3">${this.selectedLeague}</p>
                            <div class="flex items-center justify-between">
                                <div class="flex flex-col items-center w-5/12">
                                    <div class="w-12 h-12 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-center p-1.5 mb-2 shadow">
                                        <img src="${badgeL}" class="w-9 h-9 object-contain">
                                    </div>
                                    <span class="text-xs font-bold text-white">${m.local}</span>
                                </div>
                                <span class="text-xs font-black text-neutral-600">VS</span>
                                <div class="flex flex-col items-center w-5/12">
                                    <div class="w-12 h-12 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-center p-1.5 mb-2 shadow">
                                        <img src="${badgeV}" class="w-9 h-9 object-contain">
                                    </div>
                                    <span class="text-xs font-bold text-white">${m.visitante}</span>
                                </div>
                            </div>
                        </div>

                        <div class="space-y-2 mb-4">
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">Puntos proyectados (${m.local})</span>
                                <span class="font-bold text-white">${sim.ptsL} pts</span>
                            </div>
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">Puntos proyectados (${m.visitante})</span>
                                <span class="font-bold text-white">${sim.ptsV} pts</span>
                            </div>
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">Puntos totales del partido</span>
                                <span class="font-bold text-white">${sim.totalPts} pts</span>
                            </div>
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">Ganador probable</span>
                                <span class="font-bold text-white">${sim.ganador}</span>
                            </div>
                        </div>

                        <div class="glass-panel rounded-2xl p-4 text-center">
                            <p class="text-[9px] text-textMuted uppercase tracking-widest font-bold mb-3">Probabilidad de Victoria en Vivo</p>
                            <div class="flex justify-around text-center">
                                <div><div class="text-lg font-black text-white">${sim.probL}%</div><div class="text-[9px] text-textMuted uppercase">${m.local}</div></div>
                                <div class="text-neutral-600">|</div>
                                <div><div class="text-lg font-black text-white">${sim.probV}%</div><div class="text-[9px] text-textMuted uppercase">${m.visitante}</div></div>
                            </div>
                        </div>
                    `;
                    return;
                }

                if(!leagueData) {
                    container.innerHTML = `<div class="text-center py-12 text-xs text-neutral-500 uppercase tracking-widest">Próximamente datos para ${this.currentSport.toUpperCase()}</div>`;
                    return;
                }

                let html = '';
                for(const [liga, partidos] of Object.entries(leagueData)) {
                    let matches = Object.entries(partidos).filter(([k]) => this.searchQuery === '' || k.toLowerCase().includes(this.searchQuery) || liga.toLowerCase().includes(this.searchQuery));
                    if(matches.length === 0) continue;

                    html += `
                        <div class="glass-panel rounded-2xl p-4 mb-4 border border-borderSubtle">
                            <div class="flex items-center justify-between mb-3 pb-2 border-b border-borderSubtle">
                                <span class="text-xs font-bold text-white uppercase tracking-wider">${liga}</span>
                                <span class="text-[10px] text-neutral-500 font-bold">⭐</span>
                            </div>
                            <div class="space-y-3">
                    `;

                    matches.forEach(([partidoKey, datos]) => {
                        const badgeL = teamBadges[datos.local] || 'https://a.espncdn.com/i/teamlogos/soccer/500/default.png';
                        const badgeV = teamBadges[datos.visitante] || 'https://a.espncdn.com/i/teamlogos/soccer/500/default.png';

                        let timeBadgeHTML = '';
                        if(datos.estado === "EN VIVO") {
                            timeBadgeHTML = `
                                <div class="flex flex-col w-20">
                                    <div class="flex items-center space-x-1">
                                        <span class="w-2 h-2 rounded-full bg-red-500 live-dot"></span>
                                        <span class="text-[9px] text-red-400 font-extrabold uppercase">EN VIVO</span>
                                    </div>
                                    <span class="text-[10px] text-white font-bold mt-0.5">${datos.marcador}</span>
                                    <span class="text-[9px] text-neutral-400">${datos.periodo}</span>
                                </div>
                            `;
                        } else {
                            timeBadgeHTML = `<div class="w-20 text-[10px] text-neutral-400 font-semibold">${datos.hora}</div>`;
                        }

                        html += `
                            <div class="flex items-center justify-between py-2 border-b border-neutral-900/50 last:border-0">
                                ${timeBadgeHTML}
                                <div class="flex-1 space-y-2 px-2">
                                    <div class="flex items-center space-x-2">
                                        <img src="${badgeL}" class="w-5 h-5 object-contain">
                                        <span class="text-xs font-bold text-white truncate">${datos.local}</span>
                                    </div>
                                    <div class="flex items-center space-x-2">
                                        <img src="${badgeV}" class="w-5 h-5 object-contain">
                                        <span class="text-xs font-bold text-white truncate">${datos.visitante}</span>
                                    </div>
                                </div>
                                <button onclick="app.openDetail('${liga}', '${partidoKey}')" class="px-3 py-1.5 rounded-xl bg-neutral-900 border border-neutral-700 text-[10px] font-extrabold text-white tracking-wider hover:bg-neutral-800 transition-all shadow">
                                    + IA
                                </button>
                            </div>
                        `;
                    });

                    html += `</div></div>`;
                }

                container.innerHTML = html || `<div class="text-center py-12 text-xs text-neutral-500 uppercase tracking-widest">No se encontraron encuentros</div>`;
            }
        }

        const app = new SimuladorApp();
    </script>
</body>
</html>
"""

st.components.v1.html(html_code, height=850, scrolling=True)
