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
    </style>
</head>
<body class="min-h-screen pb-32 selection:bg-neutral-800 selection:text-white">

    <!-- Header Estilo Astra AI -->
    <header class="sticky top-0 z-50 glass-panel border-b border-borderSubtle px-4 py-3">
        <div class="max-w-md mx-auto flex items-center justify-between">
            <div class="flex items-center space-x-2.5 cursor-pointer" onclick="app.goHome()">
                <div class="w-8 h-8 rounded-xl bg-neutral-900 border border-neutral-700 flex items-center justify-center text-sm shadow-inner">
                    ⚽
                </div>
                <div>
                    <h1 class="font-extrabold text-sm tracking-wider text-white uppercase leading-tight">Simulador<span class="text-neutral-400">Ny</span></h1>
                    <p class="text-[8px] text-textMuted uppercase tracking-widest font-bold">Analysis AI</p>
                </div>
            </div>
            <div class="flex items-center space-x-2">
                <span class="text-[10px] px-2.5 py-1 rounded-full bg-neutral-900 border border-neutral-800 text-textMuted font-bold">Mis partidos</span>
            </div>
        </div>
    </header>

    <main class="max-w-md mx-auto px-4 pt-4">
        <!-- Buscador -->
        <div class="relative mb-4">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-neutral-500 text-xs">🔍</span>
            <input type="text" id="search-input" oninput="app.setSearch(this.value)" placeholder="Buscar equipos o ligas..." 
                class="w-full bg-cardBg border border-borderSubtle text-textLight text-xs rounded-xl pl-9 pr-4 py-2.5 focus:outline-none focus:border-neutral-500 placeholder-neutral-500 shadow-md">
        </div>

        <div id="app-content"></div>
    </main>

    <!-- Barra de Deportes Flotante Inferior (Estilo Astra AI) -->
    <nav class="fixed bottom-0 left-0 right-0 z-50 bg-[#0b0d10]/95 backdrop-blur-xl border-t border-borderSubtle px-3 py-3">
        <div class="max-w-md mx-auto grid grid-cols-5 gap-1.5 text-center">
            <button onclick="app.setSport('futbol')" id="pill-futbol" class="sport-pill active py-2 rounded-xl flex flex-col items-center justify-center space-y-1">
                <span class="text-base">⚽</span>
                <span class="text-[9px] uppercase font-bold tracking-wider">Fútbol</span>
            </button>
            <button onclick="app.setSport('nhl')" id="pill-nhl" class="sport-pill py-2 rounded-xl flex flex-col items-center justify-center space-y-1 text-neutral-400">
                <span class="text-base">🏒</span>
                <span class="text-[9px] uppercase font-bold tracking-wider">NHL</span>
            </button>
            <button onclick="app.setSport('nba')" id="pill-nba" class="sport-pill py-2 rounded-xl flex flex-col items-center justify-center space-y-1 text-neutral-400">
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
        // URLs directas de escudos oficiales estables
        const teamBadges = {
            "LA Galaxy": "https://a.espncdn.com/i/teamlogos/soccer/500/189.png",
            "Inter Miami": "https://a.espncdn.com/i/teamlogos/soccer/500/18226.png",
            "LAFC": "https://a.espncdn.com/i/teamlogos/soccer/500/15707.png",
            "NYCFC": "https://a.espncdn.com/i/teamlogos/soccer/500/17592.png",
            "Seattle": "https://a.espncdn.com/i/teamlogos/soccer/500/9891.png",
            "Portland": "https://a.espncdn.com/i/teamlogos/soccer/500/9773.png",
            "Atlanta": "https://a.espncdn.com/i/teamlogos/soccer/500/16537.png",
            "Cincinnati": "https://a.espncdn.com/i/teamlogos/soccer/500/17652.png",
            "Atlas": "https://a.espncdn.com/i/teamlogos/soccer/500/2034.png",
            "Pachuca": "https://a.espncdn.com/i/teamlogos/soccer/500/2347.png",
            "Toluca": "https://a.espncdn.com/i/teamlogos/soccer/500/2037.png",
            "Monterrey": "https://a.espncdn.com/i/teamlogos/soccer/500/2338.png",
            "Tigres": "https://a.espncdn.com/i/teamlogos/soccer/500/2343.png",
            "Cruz Azul": "https://a.espncdn.com/i/teamlogos/soccer/500/2324.png",
            "Pumas": "https://a.espncdn.com/i/teamlogos/soccer/500/2336.png",
            "America": "https://a.espncdn.com/i/teamlogos/soccer/500/2157.png",
            "Chivas": "https://a.espncdn.com/i/teamlogos/soccer/500/2322.png",
            "Leon": "https://a.espncdn.com/i/teamlogos/soccer/500/2330.png",
            "Arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png",
            "Chelsea": "https://a.espncdn.com/i/teamlogos/soccer/500/363.png",
            "Man City": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
            "Liverpool": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
            "Man United": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
            "Tottenham": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
            "Real Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
            "Barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png",
            "Atletico": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
            "Sevilla": "https://a.espncdn.com/i/teamlogos/soccer/500/243.png",
            "Inter Milan": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
            "AC Milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
            "Juventus": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
            "Napoli": "https://a.espncdn.com/i/teamlogos/soccer/500/114.png",
            "Bayern": "https://a.espncdn.com/i/teamlogos/soccer/500/132.png",
            "Dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png",
            "PSG": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
            "Marseille": "https://a.espncdn.com/i/teamlogos/soccer/500/176.png",
            "Boca Juniors": "https://a.espncdn.com/i/teamlogos/soccer/500/21.png",
            "River Plate": "https://a.espncdn.com/i/teamlogos/soccer/500/25.png",
            "Flamengo": "https://a.espncdn.com/i/teamlogos/soccer/500/2357.png",
            "Palmeiras": "https://a.espncdn.com/i/teamlogos/soccer/500/2032.png"
        };

        const sportsData = {
            "futbol": {
                "🇺🇸 MLS, Estados Unidos": {
                    "LA Galaxy vs Inter Miami": { local: "LA Galaxy", visitante: "Inter Miami", hora: "4:00 p.m.", xg_l: 1.75, xg_v: 1.90, corn_l: 6.3, corn_v: 6.7, tarjetas: 4 },
                    "LAFC vs NYCFC": { local: "LAFC", visitante: "NYCFC", hora: "6:00 p.m.", xg_l: 1.80, xg_v: 1.25, corn_l: 6.5, corn_v: 4.5, tarjetas: 3 }
                },
                "🇲🇽 Liga MX, México": {
                    "Atlas vs Pachuca": { local: "Atlas", visitante: "Pachuca", hora: "4:00 p.m.", xg_l: 1.15, xg_v: 1.40, corn_l: 5.1, corn_v: 5.5, tarjetas: 5 },
                    "Tigres vs Cruz Azul": { local: "Tigres", visitante: "Cruz Azul", hora: "6:00 p.m.", xg_l: 1.45, xg_v: 1.35, corn_l: 5.5, corn_v: 5.2, tarjetas: 6 },
                    "Toluca vs Monterrey": { local: "Toluca", visitante: "Monterrey", hora: "6:00 p.m.", xg_l: 1.55, xg_v: 1.50, corn_l: 6.0, corn_v: 5.8, tarjetas: 4 },
                    "Pumas vs America": { local: "Pumas", visitante: "America", hora: "8:10 p.m.", xg_l: 1.20, xg_v: 1.65, corn_l: 4.8, corn_v: 6.2, tarjetas: 5 }
                },
                "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League, Inglaterra": {
                    "Arsenal vs Chelsea": { local: "Arsenal", visitante: "Chelsea", hora: "7:30 a.m.", xg_l: 1.75, xg_v: 1.15, corn_l: 6.4, corn_v: 4.9, tarjetas: 4 },
                    "Man City vs Liverpool": { local: "Man City", visitante: "Liverpool", hora: "10:00 a.m.", xg_l: 1.90, xg_v: 1.65, corn_l: 7.1, corn_v: 5.8, tarjetas: 5 }
                },
                "🇪🇸 LaLiga, España": {
                    "Real Madrid vs Barcelona": { local: "Real Madrid", visitante: "Barcelona", hora: "2:00 p.m.", xg_l: 1.80, xg_v: 1.70, corn_l: 6.2, corn_v: 5.9, tarjetas: 6 }
                }
            },
            "nba": {
                "🇺🇸 NBA, Estados Unidos": {
                    "Indiana Pacers vs Denver Nuggets": { local: "Indiana", visitante: "Denver", hora: "3:00 p.m.", xg_l: 112, xg_v: 115, corn_l: 0, corn_v: 0, tarjetas: 0 },
                    "Atlanta Hawks vs Brooklyn Nets": { local: "Atlanta", visitante: "Brooklyn", hora: "5:30 p.m.", xg_l: 108, xg_v: 110, corn_l: 0, corn_v: 0, tarjetas: 0 }
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

            poissonRandom(lambda) {
                let L = Math.exp(-lambda), k = 0, p = 1;
                do { k++; p *= Math.random(); } while (p > L);
                return k - 1;
            }

            runMonteCarlo(xg_l, xg_v) {
                const sims = 10000;
                let wL = 0, d = 0, wV = 0, btts = 0;
                for(let i=0; i<sims; i++) {
                    let gL = this.poissonRandom(xg_l), gV = this.poissonRandom(xg_v);
                    if(gL > gV) wL++; else if(gL === gV) d++; else wV++;
                    if(gL > 0 && gV > 0) btts++;
                }
                return {
                    probL: Math.round((wL/sims)*100),
                    probX: Math.round((d/sims)*100),
                    probV: Math.round((wV/sims)*100),
                    probBtts: Math.round((btts/sims)*100)
                };
            }

            render() {
                const container = document.getElementById('app-content');
                const leagueData = sportsData[this.currentSport];

                if(this.currentView === 'detail') {
                    const m = sportsData['futbol'][this.selectedLeague][this.selectedMatch];
                    const badgeL = teamBadges[m.local] || 'https://a.espncdn.com/i/teamlogos/soccer/500/default.png';
                    const badgeV = teamBadges[m.visitante] || 'https://a.espncdn.com/i/teamlogos/soccer/500/default.png';
                    const sim = this.runMonteCarlo(m.xg_l, m.xg_v);
                    const ganador = sim.probL >= sim.probV ? m.local : m.visitante;

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
                                    <span class="text-[9px] text-neutral-400 mt-0.5">xG ${m.xg_l}</span>
                                </div>
                                <span class="text-xs font-black text-neutral-600">VS</span>
                                <div class="flex flex-col items-center w-5/12">
                                    <div class="w-12 h-12 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-center p-1.5 mb-2 shadow">
                                        <img src="${badgeV}" class="w-9 h-9 object-contain">
                                    </div>
                                    <span class="text-xs font-bold text-white">${m.visitante}</span>
                                    <span class="text-[9px] text-neutral-400 mt-0.5">xG ${m.xg_v}</span>
                                </div>
                            </div>
                        </div>

                        <div class="space-y-2 mb-4">
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">Tarjetas amarillas proyectadas</span>
                                <span class="font-bold text-white">${m.tarjetas}</span>
                            </div>
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">Tiros de esquina (Córners)</span>
                                <span class="font-bold text-white">${(m.corn_l + m.corn_v).toFixed(1)}</span>
                            </div>
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">Ambos equipos marcarán (BTTS)</span>
                                <span class="font-bold text-white">${sim.probBtts > 50 ? 'Sí' : 'No'} (${sim.probBtts}%)</span>
                            </div>
                            <div class="match-card rounded-xl p-3 flex justify-between items-center text-xs">
                                <span class="text-textMuted">Ganador probable</span>
                                <span class="font-bold text-white">${ganador}</span>
                            </div>
                        </div>

                        <div class="glass-panel rounded-2xl p-4 text-center">
                            <p class="text-[9px] text-textMuted uppercase tracking-widest font-bold mb-3">Probabilidad de Victoria en Vivo</p>
                            <div class="flex justify-around text-center">
                                <div><div class="text-lg font-black text-white">${sim.probL}%</div><div class="text-[9px] text-textMuted uppercase">${m.local}</div></div>
                                <div class="text-neutral-600">|</div>
                                <div><div class="text-lg font-black text-white">${sim.probX}%</div><div class="text-[9px] text-textMuted uppercase">Empate</div></div>
                                <div class="text-neutral-600">|</div>
                                <div><div class="text-lg font-black text-white">${sim.probV}%</div><div class="text-[9px] text-textMuted uppercase">${m.visitante}</div></div>
                            </div>
                        </div>
                    `;
                    return;
                }

                if(!leagueData) {
                    container.innerHTML = `<div class="text-center py-12 text-xs text-neutral-500 uppercase tracking-widest">Sección en desarrollo para ${this.currentSport.toUpperCase()}</div>`;
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

                        html += `
                            <div class="flex items-center justify-between py-1.5 border-b border-neutral-900/50 last:border-0">
                                <div class="w-16 text-[10px] text-neutral-400 font-semibold">${datos.hora || 'En vivo'}</div>
                                <div class="flex-1 space-y-2">
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
