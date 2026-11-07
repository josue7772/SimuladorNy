import streamlit as st

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

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
                <div class="w-8 h-8 rounded-xl bg-neutral-900 border border-neutral-700 flex items-center justify-center text-sm shadow-inner" id="header-icon">
                    ⚽
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
        <div class="max-w-md mx-auto grid grid-cols-4 gap-2 text-center">
            <button onclick="app.setSport('futbol')" id="pill-futbol" class="sport-pill active py-2.5 rounded-xl flex flex-col items-center justify-center space-y-1">
                <span class="text-base">⚽</span>
                <span class="text-[9px] uppercase font-bold tracking-wider">Fútbol</span>
            </button>
            <button onclick="app.setSport('nba')" id="pill-nba" class="sport-pill py-2.5 rounded-xl flex flex-col items-center justify-center space-y-1 text-neutral-400">
                <span class="text-base">🏀</span>
                <span class="text-[9px] uppercase font-bold tracking-wider">NBA</span>
            </button>
            <button onclick="app.setSport('kbo')" id="pill-kbo" class="sport-pill py-2.5 rounded-xl flex flex-col items-center justify-center space-y-1 text-neutral-400">
                <span class="text-base">⚾</span>
                <span class="text-[9px] uppercase font-bold tracking-wider">KBO</span>
            </button>
            <button onclick="app.setSport('nhl')" id="pill-nhl" class="sport-pill py-2.5 rounded-xl flex flex-col items-center justify-center space-y-1 text-neutral-400">
                <span class="text-base">🏒</span>
                <span class="text-[9px] uppercase font-bold tracking-wider">NHL</span>
            </button>
        </div>
    </nav>

    <script>
        const sportsData = {
            "futbol": {
                "🇲🇽 México · Liga MX": {
                    "Nax vs Pumas": { local: "Nax", visitante: "Pumas", estado: "EN VIVO", periodo: "En juego", base_l: 1.2, base_v: 1.1, sport: "futbol", metric1_lbl: "Tarjetas amarillas", metric1_val: "4", metric2_lbl: "Córners", metric2_val: "9.5" }
                },
                "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra · Premier League": {
                    "Arsenal vs Chelsea": { local: "Arsenal", visitante: "Chelsea", hora: "Programado", base_l: 1.75, base_v: 1.15, sport: "futbol", metric1_lbl: "Tarjetas amarillas", metric1_val: "4", metric2_lbl: "Córners", metric2_val: "11.4" }
                },
                "🇪🇸 España · LaLiga": {
                    "Real Madrid vs Barcelona": { local: "Real Madrid", visitante: "Barcelona", hora: "Programado", base_l: 1.80, base_v: 1.70, sport: "futbol", metric1_lbl: "Tarjetas amarillas", metric1_val: "6", metric2_lbl: "Córners", metric2_val: "11.0" }
                },
                "🇮🇹 Italia · Serie A": {
                    "Inter vs Milan": { local: "Inter", visitante: "Milan", hora: "Programado", base_l: 1.50, base_v: 1.30, sport: "futbol", metric1_lbl: "Tarjetas amarillas", metric1_val: "5", metric2_lbl: "Córners", metric2_val: "10.2" }
                },
                "🇪🇺 UEFA · Champions League": {
                    "Bayern vs PSG": { local: "Bayern", visitante: "PSG", hora: "Programado", base_l: 1.85, base_v: 1.60, sport: "futbol", metric1_lbl: "Tarjetas amarillas", metric1_val: "4", metric2_lbl: "Córners", metric2_val: "10.8" }
                }
            },
            "nba": {
                "🇺🇸 NBA, Estados Unidos": {
                    "Nuggets vs Pacers": { local: "Nuggets", visitante: "Pacers", estado: "EN VIVO", periodo: "En curso", base_l: 114.5, base_v: 104.0, sport: "nba" },
                    "Nets vs Hawks": { local: "Nets", visitante: "Hawks", hora: "Programado", base_l: 108.0, base_v: 112.5, sport: "nba" },
                    "Knicks vs Cavaliers": { local: "Knicks", visitante: "Cavaliers", hora: "Programado", base_l: 110.0, base_v: 113.0, sport: "nba" },
                    "Wizards vs Thunder": { local: "Wizards", visitante: "Thunder", hora: "Programado", base_l: 105.5, base_v: 119.0, sport: "nba" },
                    "Magic vs Warriors": { local: "Magic", visitante: "Warriors", hora: "Programado", base_l: 107.0, base_v: 112.0, sport: "nba" },
                    "Rockets vs Suns": { local: "Rockets", visitante: "Suns", hora: "Programado", base_l: 111.0, base_v: 114.5, sport: "nba" },
                    "Spurs vs Trail Blazers": { local: "Spurs", visitante: "Trail Blazers", hora: "Programado", base_l: 109.0, base_v: 107.5, sport: "nba" }
                }
            },
            "kbo": {
                "🇰🇷 KBO League, Corea del Sur": {
                    "Doosan Bears vs LG Twins": { local: "Doosan Bears", visitante: "LG Twins", hora: "Programado", base_l: 4.5, base_v: 5.0, sport: "kbo" },
                    "KIA Tigers vs Samsung Lions": { local: "KIA Tigers", visitante: "Samsung Lions", hora: "Programado", base_l: 5.2, base_v: 4.8, sport: "kbo" }
                }
            },
            "nhl": {
                "🇨🇦🇺🇸 NHL, Hockey sobre Hielo": {
                    "Maple Leafs vs Canadiens": { local: "Maple Leafs", visitante: "Canadiens", hora: "Programado", base_l: 3.5, base_v: 2.8, sport: "nhl" },
                    "Rangers vs Bruins": { local: "Rangers", visitante: "Bruins", hora: "Programado", base_l: 3.2, base_v: 3.4, sport: "nhl" }
                }
            }
        };

        class SimuladorApp {
            constructor() {
                this.currentSport = 'futbol';
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
                ['futbol', 'nba', 'kbo', 'nhl'].forEach(s => {
                    const el = document.getElementById(`pill-${s}`);
                    if(el) {
                        if(s === sport) el.className = "sport-pill active py-2.5 rounded-xl flex flex-col items-center justify-center space-y-1";
                        else el.className = "sport-pill py-2.5 rounded-xl flex flex-col items-center justify-center space-y-1 text-neutral-400";
                    }
                });
                const icons = { 'futbol': '⚽', 'nba': '🏀', 'kbo': '⚾', 'nhl': '🏒' };
                document.getElementById('header-icon').innerText = icons[sport] || '⚽';
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

            runSoccerSimulation(m) {
                let poissonRandom = (lambda) => {
                    let L = Math.exp(-lambda), k = 0, p = 1;
                    do { k++; p *= Math.random(); } while (p > L);
                    return k - 1;
                };
                const sims = 10000;
                let wL = 0, d = 0, wV = 0;
                for(let i=0; i<sims; i++) {
                    let gL = poissonRandom(m.base_l), gV = poissonRandom(m.base_v);
                    if(gL > gV) wL++; else if(gL === gV) d++; else wV++;
                }
                return {
                    ganador: wL >= wV ? m.local : m.visitante,
                    probL: Math.round((wL/sims)*100),
                    probX: Math.round((d/sims)*100),
                    probV: Math.round((wV/sims)*100),
                    metric1_lbl: m.metric1_lbl, metric1_val: m.metric1_val,
                    metric2_lbl: m.metric2_lbl, metric2_val: m.metric2_val
                };
            }

            runNBASimulation(m) {
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
            }

            runGenericSimulation(m) {
                let simL = (m.base_l + Math.random() * 1.5).toFixed(1);
                let simV = (m.base_v + Math.random() * 1.5).toFixed(1);
                let total = (parseFloat(simL) + parseFloat(simV)).toFixed(1);
                let probL = parseFloat(simL) >= parseFloat(simV) ? 55 : 45;
                return {
                    ptsL: simL,
                    ptsV: simV,
                    totalPts: total,
                    ganador: parseFloat(simL) >= parseFloat(simV) ? m.local : m.visitante,
                    probL: probL,
                    probV: 100 - probL
                };
            }

            render() {
                const container = document.getElementById('app-content');
                const leagueData = sportsData[this.currentSport];

                if(this.currentView === 'detail') {
                    const m = sportsData[this.currentSport][this.selectedLeague][this.selectedMatch];
                    let statsHTML = '';
                    let probHTML = '';

                    if(m.sport === 'nba') {
                        const sim = this.runNBASimulation(m);
                        statsHTML = `
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
                        `;
                        probHTML = `
                            <div class="flex justify-around text-center">
                                <div><div class="text-lg font-black text-white">${sim.probL}%</div><div class="text-[9px] text-textMuted uppercase">${m.local}</div></div>
                                <div class="text-neutral-600">|</div>
                                <div><div class="text-lg font-black text-white">${sim.probV}%</div><div class="text-[9px] text-textMuted uppercase">${m.visitante}</div></div>
                            </div>
                        `;
                    } else if(m.sport === 'kbo' || m.sport === 'nhl') {
                        const sim = this.runGenericSimulation(m);
                        statsHTML = `
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">Carreras/Goles (${m.local})</span>
                                <span class="font-bold text-white">${sim.ptsL}</span>
                            </div>
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">Carreras/Goles (${m.visitante})</span>
                                <span class="font-bold text-white">${sim.ptsV}</span>
                            </div>
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">Total estimado</span>
                                <span class="font-bold text-white">${sim.totalPts}</span>
                            </div>
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">Ganador probable</span>
                                <span class="font-bold text-white">${sim.ganador}</span>
                            </div>
                        `;
                        probHTML = `
                            <div class="flex justify-around text-center">
                                <div><div class="text-lg font-black text-white">${sim.probL}%</div><div class="text-[9px] text-textMuted uppercase">${m.local}</div></div>
                                <div class="text-neutral-600">|</div>
                                <div><div class="text-lg font-black text-white">${sim.probV}%</div><div class="text-[9px] text-textMuted uppercase">${m.visitante}</div></div>
                            </div>
                        `;
                    } else {
                        const sim = this.runSoccerSimulation(m);
                        statsHTML = `
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">${sim.metric1_lbl}</span>
                                <span class="font-bold text-white">${sim.metric1_val}</span>
                            </div>
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">${sim.metric2_lbl}</span>
                                <span class="font-bold text-white">${sim.metric2_val}</span>
                            </div>
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">Ganador probable</span>
                                <span class="font-bold text-white">${sim.ganador}</span>
                            </div>
                        `;
                        probHTML = `
                            <div class="flex justify-around text-center">
                                <div><div class="text-lg font-black text-white">${sim.probL}%</div><div class="text-[9px] text-textMuted uppercase">${m.local}</div></div>
                                <div class="text-neutral-600">|</div>
                                <div><div class="text-lg font-black text-white">${sim.probX}%</div><div class="text-[9px] text-textMuted uppercase">Empate</div></div>
                                <div class="text-neutral-600">|</div>
                                <div><div class="text-lg font-black text-white">${sim.probV}%</div><div class="text-[9px] text-textMuted uppercase">${m.visitante}</div></div>
                            </div>
                        `;
                    }

                    container.innerHTML = `
                        <button onclick="app.goHome()" class="mb-4 text-xs font-semibold px-3 py-1.5 rounded-xl bg-cardBg border border-borderSubtle text-textLight">← Volver</button>
                        <div class="glass-panel rounded-2xl p-5 mb-4 text-center">
                            <p class="text-[9px] text-textMuted uppercase tracking-widest font-bold mb-3">${this.selectedLeague}</p>
                            <div class="flex items-center justify-between">
                                <div class="flex flex-col items-center w-5/12">
                                    <span class="text-sm font-bold text-white mb-2">${m.local}</span>
                                </div>
                                <span class="text-xs font-black text-neutral-600">VS</span>
                                <div class="flex flex-col items-center w-5/12">
                                    <span class="text-sm font-bold text-white mb-2">${m.visitante}</span>
                                </div>
                            </div>
                        </div>

                        <div class="space-y-2 mb-4">
                            ${statsHTML}
                        </div>

                        <div class="glass-panel rounded-2xl p-4 text-center">
                            <p class="text-[9px] text-textMuted uppercase tracking-widest font-bold mb-3">Probabilidad de Victoria en Vivo</p>
                            ${probHTML}
                        </div>
                    `;
                    return;
                }

                if(!leagueData) {
                    container.innerHTML = `<div class="text-center py-12 text-xs text-neutral-500 uppercase tracking-widest">Próximamente datos</div>`;
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
                        let timeBadgeHTML = '';
                        if(datos.estado === "EN VIVO") {
                            timeBadgeHTML = `
                                <div class="flex flex-col w-24">
                                    <div class="flex items-center space-x-1">
                                        <span class="w-2 h-2 rounded-full bg-red-500 live-dot"></span>
                                        <span class="text-[9px] text-red-400 font-extrabold uppercase">EN VIVO</span>
                                    </div>
                                    <span class="text-[9px] text-neutral-400 font-semibold mt-1">${datos.periodo}</span>
                                </div>
                            `;
                        } else {
                            timeBadgeHTML = `<div class="w-24 text-[10px] text-neutral-400 font-semibold">${datos.hora || 'Programado'}</div>`;
                        }

                        html += `
                            <div class="flex items-center justify-between py-2 border-b border-neutral-900/50 last:border-0">
                                ${timeBadgeHTML}
                                <div class="flex-1 space-y-2 px-2">
                                    <div class="flex items-center space-x-2">
                                        <span class="text-xs font-bold text-white truncate">${datos.local}</span>
                                    </div>
                                    <div class="flex items-center space-x-2">
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
