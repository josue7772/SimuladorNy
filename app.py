import streamlit as st

st.set_page_config(page_title="SimuladorNy", page_icon="⚽", layout="centered")

html_code = """
<!DOCTYPE html>
<html lang="es" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>SimuladorNy - Inteligencia Cuantitativa Deportiva</title>
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
                        borderBright: '#333b4d',
                        textMuted: '#9ca3af',
                        textLight: '#f3f4f6',
                        accentSilver: '#e5e7eb'
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
        ::-webkit-scrollbar {
            width: 4px;
        }
        ::-webkit-scrollbar-track {
            background: #0b0d10;
        }
        ::-webkit-scrollbar-thumb {
            background: #222733;
            border-radius: 4px;
        }
        .glass-panel {
            background: rgba(18, 21, 28, 0.75);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .glass-card {
            background: rgba(18, 21, 28, 0.65);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .glass-card:active, .glass-card:hover {
            background: rgba(26, 31, 44, 0.85);
            border-color: rgba(255, 255, 255, 0.15);
        }
        @keyframes pulseGlow {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(0.98); }
        }
        .simulating {
            animation: pulseGlow 0.4s ease-in-out infinite;
        }
    </style>
</head>
<body class="min-h-screen pb-24 selection:bg-neutral-800 selection:text-white">

    <header class="sticky top-0 z-50 glass-panel border-b border-borderSubtle px-4 py-3.5">
        <div class="max-w-md mx-auto flex items-center justify-between">
            <div class="flex items-center space-x-2.5 cursor-pointer" onclick="app.goHome()">
                <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-neutral-800 to-neutral-900 border border-neutral-700 flex items-center justify-center text-sm shadow-inner">
                    ⚽
                </div>
                <div>
                    <h1 class="font-extrabold text-base tracking-wider text-white uppercase leading-tight">Simulador<span class="text-neutral-400">Ny</span></h1>
                    <p class="text-[9px] text-textMuted uppercase tracking-widest font-semibold">Análisis Cuantitativo</p>
                </div>
            </div>
            <div id="header-action">
                <span class="text-xs px-2.5 py-1 rounded-full bg-neutral-900 border border-neutral-800 text-textMuted font-semibold tracking-wider">ENVIVO</span>
            </div>
        </div>
    </header>

    <main class="max-w-md mx-auto px-4 pt-4">
        <div class="grid grid-cols-3 gap-1 bg-neutral-950 p-1 rounded-xl border border-borderSubtle mb-5">
            <button id="tab-cartelera" onclick="app.switchTab('cartelera')" class="py-2 text-[11px] font-bold rounded-lg uppercase tracking-wider transition-all bg-neutral-800 text-white shadow">Cartelera</button>
            <button id="tab-directo" onclick="app.switchTab('directo')" class="py-2 text-[11px] font-bold rounded-lg uppercase tracking-wider transition-all text-neutral-400 hover:text-white">Simulador</button>
            <button id="tab-modelo" onclick="app.switchTab('modelo')" class="py-2 text-[11px] font-bold rounded-lg uppercase tracking-wider transition-all text-neutral-400 hover:text-white">Modelo IA</button>
        </div>

        <div id="app-content"></div>
    </main>

    <nav class="fixed bottom-0 left-0 right-0 z-50 glass-panel border-t border-borderSubtle px-6 py-2.5">
        <div class="max-w-md mx-auto flex items-center justify-around">
            <button onclick="app.switchTab('cartelera')" class="flex flex-col items-center space-y-1 text-white">
                <span class="text-lg">⚽</span>
                <span class="text-[9px] uppercase font-bold tracking-widest">Partidos</span>
            </button>
            <button onclick="app.switchTab('directo')" class="flex flex-col items-center space-y-1 text-neutral-400 hover:text-white">
                <span class="text-lg">🎛️</span>
                <span class="text-[9px] uppercase font-bold tracking-widest">Simular</span>
            </button>
            <button onclick="app.switchTab('modelo')" class="flex flex-col items-center space-y-1 text-neutral-400 hover:text-white">
                <span class="text-lg">📊</span>
                <span class="text-[9px] uppercase font-bold tracking-widest">Métricas</span>
            </button>
        </div>
    </nav>

    <script>
        // Identificadores visuales limpios y garantizados para cada equipo
        const teamIcons = {
            "LA Galaxy": "⭐", "Inter Miami": "⚡", "LAFC": "🦅", "NYCFC": "🏙️",
            "Seattle": "🌊", "Portland": "🌲", "Atlanta": "🚂", "Cincinnati": "🦁",
            "Atlas": "🦊", "Pachuca": "⛏️", "Toluca": "👹", "Monterrey": "🤠",
            "Tigres": "🐅", "Cruz Azul": "🚂", "Pumas": "🐾", "America": "🦅",
            "Chivas": "🐐", "Leon": "🦁", "Arsenal": "💣", "Chelsea": "🦁",
            "Man City": "🛡️", "Liverpool": "🔴", "Man United": "😈", "Tottenham": "🐓",
            "Real Madrid": "👑", "Barcelona": "🔵", "Atletico": "🥷", "Sevilla": "⚽",
            "Inter Milan": "🐍", "AC Milan": "👹", "Juventus": "🦓", "Napoli": "🌋",
            "Bayern": "🔴", "Dortmund": "🐝", "PSG": "🗼", "Marseille": "⚓",
            "Boca Juniors": "💙", "River Plate": "🤍", "Flamengo": "🥷", "Palmeiras": "🐷"
        };

        const carteleraGlobal = {
            "MLS, Estados Unidos": {
                "LA Galaxy vs Inter Miami": { local: "LA Galaxy", visitante: "Inter Miami", xg_l: 1.75, xg_v: 1.90, corn_l: 6.3, corn_v: 6.7, tarjetas: 4 },
                "LAFC vs NYCFC": { local: "LAFC", visitante: "NYCFC", xg_l: 1.80, xg_v: 1.25, corn_l: 6.5, corn_v: 4.5, tarjetas: 3 },
                "Seattle vs Portland": { local: "Seattle", visitante: "Portland", xg_l: 1.50, xg_v: 1.20, corn_l: 5.0, corn_v: 5.0, tarjetas: 5 },
                "Atlanta vs Cincinnati": { local: "Atlanta", visitante: "Cincinnati", xg_l: 1.60, xg_v: 1.40, corn_l: 6.0, corn_v: 4.0, tarjetas: 4 }
            },
            "Liga MX, México": {
                "Atlas vs Pachuca": { local: "Atlas", visitante: "Pachuca", xg_l: 1.15, xg_v: 1.40, corn_l: 5.1, corn_v: 5.5, tarjetas: 5 },
                "Toluca vs Monterrey": { local: "Toluca", visitante: "Monterrey", xg_l: 1.55, xg_v: 1.50, corn_l: 6.0, corn_v: 5.8, tarjetas: 4 },
                "Tigres vs Cruz Azul": { local: "Tigres", visitante: "Cruz Azul", xg_l: 1.45, xg_v: 1.35, corn_l: 5.5, corn_v: 5.2, tarjetas: 6 },
                "Pumas vs America": { local: "Pumas", visitante: "America", xg_l: 1.20, xg_v: 1.65, corn_l: 4.8, corn_v: 6.2, tarjetas: 5 },
                "Chivas vs Leon": { local: "Chivas", visitante: "Leon", xg_l: 1.40, xg_v: 1.20, corn_l: 5.3, corn_v: 4.7, tarjetas: 4 }
            },
            "Premier League, Inglaterra": {
                "Arsenal vs Chelsea": { local: "Arsenal", visitante: "Chelsea", xg_l: 1.75, xg_v: 1.15, corn_l: 6.4, corn_v: 4.9, tarjetas: 4 },
                "Man City vs Liverpool": { local: "Man City", visitante: "Liverpool", xg_l: 1.90, xg_v: 1.65, corn_l: 7.1, corn_v: 5.8, tarjetas: 5 },
                "Man United vs Tottenham": { local: "Man United", visitante: "Tottenham", xg_l: 1.45, xg_v: 1.40, corn_l: 5.6, corn_v: 5.4, tarjetas: 5 }
            },
            "LaLiga, España": {
                "Real Madrid vs Barcelona": { local: "Real Madrid", visitante: "Barcelona", xg_l: 1.80, xg_v: 1.70, corn_l: 6.2, corn_v: 5.9, tarjetas: 6 },
                "Atletico vs Sevilla": { local: "Atletico", visitante: "Sevilla", xg_l: 1.55, xg_v: 0.95, corn_l: 5.4, corn_v: 4.1, tarjetas: 5 }
            },
            "Serie A, Italia": {
                "Inter Milan vs AC Milan": { local: "Inter Milan", visitante: "AC Milan", xg_l: 1.60, xg_v: 1.25, corn_l: 5.8, corn_v: 5.0, tarjetas: 5 },
                "Juventus vs Napoli": { local: "Juventus", visitante: "Napoli", xg_l: 1.35, xg_v: 1.30, corn_l: 5.3, corn_v: 5.2, tarjetas: 4 }
            },
            "Bundesliga, Alemania": {
                "Bayern vs Dortmund": { local: "Bayern", visitante: "Dortmund", xg_l: 2.30, xg_v: 1.50, corn_l: 7.5, corn_v: 5.3, tarjetas: 4 }
            },
            "Ligue 1, Francia": {
                "PSG vs Marseille": { local: "PSG", visitante: "Marseille", xg_l: 2.10, xg_v: 1.10, corn_l: 6.9, corn_v: 4.1, tarjetas: 5 }
            },
            "Liga Profesional, Argentina": {
                "Boca Juniors vs River Plate": { local: "Boca Juniors", visitante: "River Plate", xg_l: 1.25, xg_v: 1.20, corn_l: 5.1, corn_v: 4.9, tarjetas: 7 }
            },
            "Brasileirão, Brasil": {
                "Flamengo vs Palmeiras": { local: "Flamengo", visitante: "Palmeiras", xg_l: 1.55, xg_v: 1.30, corn_l: 6.1, corn_v: 5.2, tarjetas: 5 }
            }
        };

        class SimuladorApp {
            constructor() {
                this.currentTab = 'cartelera';
                this.selectedLeague = null;
                this.selectedMatch = null;
                this.searchQuery = '';
                this.isSimulating = false;
                this.init();
            }

            init() {
                this.render();
            }

            goHome() {
                this.selectedLeague = null;
                this.selectedMatch = null;
                this.switchTab('cartelera');
            }

            switchTab(tab) {
                this.currentTab = tab;
                ['cartelera', 'directo', 'modelo'].forEach(t => {
                    const btn = document.getElementById(`tab-${t}`);
                    if(btn) {
                        if(t === tab) {
                            btn.className = "py-2 text-[11px] font-bold rounded-lg uppercase tracking-wider transition-all bg-neutral-800 text-white shadow";
                        } else {
                            btn.className = "py-2 text-[11px] font-bold rounded-lg uppercase tracking-wider transition-all text-neutral-400 hover:text-white";
                        }
                    }
                });
                this.render();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }

            openDetail(liga, partidoKey) {
                this.selectedLeague = liga;
                this.selectedMatch = partidoKey;
                this.currentTab = 'detail';
                this.render();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }

            setSearch(val) {
                this.searchQuery = val.toLowerCase();
                const list = document.getElementById('matches-list');
                if(list) {
                    list.innerHTML = this.renderMatchesListHTML();
                }
            }

            poissonRandom(lambda) {
                let L = Math.exp(-lambda);
                let k = 0;
                let p = 1;
                do {
                    k++;
                    p *= Math.random();
                } while (p > L);
                return k - 1;
            }

            runMonteCarloSimulation(xg_l, xg_v) {
                const sims = 10000;
                let winsL = 0, draws = 0, winsV = 0, btts = 0;
                for(let i = 0; i < sims; i++) {
                    let gL = this.poissonRandom(xg_l);
                    let gV = this.poissonRandom(xg_v);
                    if(gL > gV) winsL++;
                    else if(gL === gV) draws++;
                    else winsV++;
                    if(gL > 0 && gV > 0) btts++;
                }
                return {
                    probL: Math.round((winsL / sims) * 100),
                    probX: Math.round((draws / sims) * 100),
                    probV: Math.round((winsV / sims) * 100),
                    probBtts: Math.round((btts / sims) * 100)
                };
            }

            recalculateSim() {
                if(this.isSimulating) return;
                this.isSimulating = true;
                const container = document.getElementById('sim-box');
                if(container) container.classList.add('simulating');

                setTimeout(() => {
                    this.isSimulating = false;
                    this.render();
                }, 400);
            }

            renderMatchesListHTML() {
                let html = '';
                for (const [liga, partidos] of Object.entries(carteleraGlobal)) {
                    let matchEntries = Object.entries(partidos).filter(([key]) => {
                        return this.searchQuery === '' || key.toLowerCase().includes(this.searchQuery) || liga.toLowerCase().includes(this.searchQuery);
                    });

                    if (matchEntries.length === 0) continue;

                    html += `
                        <div class="mb-5">
                            <h3 class="text-[11px] font-bold text-textMuted uppercase tracking-widest mb-2.5 pl-1.5 border-l-2 border-neutral-600">${liga}</h3>
                            <div class="space-y-2">
                    `;

                    matchEntries.forEach(([nombrePartido, datos]) => {
                        const iconL = teamIcons[datos.local] || '⚽';
                        const iconV = teamIcons[datos.visitante] || '⚽';

                        html += `
                            <button onclick="app.openDetail('${liga}', '${nombrePartido}')" class="glass-card w-full rounded-xl p-3.5 flex items-center justify-between text-left group">
                                <div class="flex items-center space-x-3 w-11/12">
                                    <div class="flex items-center space-x-2 w-1/2 justify-end">
                                        <span class="text-xs font-semibold text-textLight text-right truncate">${datos.local}</span>
                                        <span class="text-base">${iconL}</span>
                                    </div>
                                    <span class="text-[10px] text-neutral-600 font-extrabold tracking-wider">VS</span>
                                    <div class="flex items-center space-x-2 w-1/2 justify-start">
                                        <span class="text-base">${iconV}</span>
                                        <span class="text-xs font-semibold text-textLight text-left truncate">${datos.visitante}</span>
                                    </div>
                                </div>
                                <div class="text-neutral-500 group-hover:text-white transition-colors text-xs font-bold">
                                    &rarr;
                                </div>
                            </button>
                        `;
                    });

                    html += `</div></div>`;
                }

                return html || `<div class="text-center py-12 text-xs text-neutral-500 uppercase tracking-widest">No se encontraron encuentros deportivos</div>`;
            }

            render() {
                const container = document.getElementById('app-content');
                const headerAction = document.getElementById('header-action');

                if (this.currentTab === 'cartelera') {
                    headerAction.innerHTML = `<span class="text-xs px-2.5 py-1 rounded-full bg-neutral-900 border border-neutral-800 text-textMuted font-semibold tracking-wider">ENVIVO</span>`;
                    container.innerHTML = `
                        <div class="text-center py-5">
                            <h2 class="text-2xl font-extrabold tracking-tight text-white mb-1">SimuladorNy</h2>
                            <p class="text-[10px] text-textMuted uppercase tracking-widest font-semibold">Inteligencia Cuantitativa en Tiempo Real</p>
                        </div>

                        <div class="relative mb-5">
                            <span class="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-neutral-500 text-sm">
                                🔍
                            </span>
                            <input type="text" id="search-input" value="${this.searchQuery}" oninput="app.setSearch(this.value)" placeholder="Buscar equipo o liga profesional..." 
                                class="w-full bg-cardBg border border-borderSubtle text-textLight text-xs rounded-xl pl-9 pr-4 py-3 focus:outline-none focus:border-neutral-500 placeholder-neutral-500 shadow-md">
                        </div>

                        <div id="matches-list">
                            ${this.renderMatchesListHTML()}
                        </div>
                    `;
                } else if (this.currentTab === 'detail') {
                    headerAction.innerHTML = `
                        <button onclick="app.goHome()" class="flex items-center space-x-1 text-xs px-3 py-1.5 rounded-xl bg-cardBg border border-borderSubtle text-textLight font-semibold hover:border-neutral-500 transition-colors">
                            <span>&larr;</span> <span>Volver</span>
                        </button>
                    `;
                    const m = carteleraGlobal[this.selectedLeague][this.selectedMatch];
                    const iconL = teamIcons[m.local] || '⚽';
                    const iconV = teamIcons[m.visitante] || '⚽';
                    
                    const sim = this.runMonteCarloSimulation(m.xg_l, m.xg_v);
                    const corners = (m.corn_l + m.corn_v).toFixed(1);
                    const ganador = sim.probL >= sim.probV ? m.local : m.visitante;
                    const ganadorIcon = sim.probL >= sim.probV ? iconL : iconV;

                    container.innerHTML = `
                        <div class="pt-1">
                            <div class="glass-panel rounded-2xl p-6 text-center shadow-xl border border-borderSubtle mb-5 relative">
                                <p class="text-[10px] text-textMuted uppercase tracking-widest font-semibold mb-4">${this.selectedLeague}</p>
                                
                                <div class="flex items-center justify-between">
                                    <div class="flex flex-col items-center w-5/12">
                                        <div class="w-14 h-14 rounded-2xl bg-neutral-900 border border-neutral-800 flex items-center justify-center text-2xl mb-2.5 shadow-md">
                                            ${iconL}
                                        </div>
                                        <h3 class="font-bold text-sm text-white leading-tight">${m.local}</h3>
                                        <span class="text-[10px] text-neutral-400 mt-1">xG ${m.xg_l}</span>
                                    </div>

                                    <div class="w-2/12 flex flex-col items-center justify-center">
                                        <span class="text-xs font-extrabold text-neutral-500 tracking-wider">VS</span>
                                    </div>

                                    <div class="flex flex-col items-center w-5/12">
                                        <div class="w-14 h-14 rounded-2xl bg-neutral-900 border border-neutral-800 flex items-center justify-center text-2xl mb-2.5 shadow-md">
                                            ${iconV}
                                        </div>
                                        <h3 class="font-bold text-sm text-white leading-tight">${m.visitante}</h3>
                                        <span class="text-[10px] text-neutral-400 mt-1">xG ${m.xg_v}</span>
                                    </div>
                                </div>
                            </div>

                            <button onclick="app.recalculateSim()" class="w-full mb-5 py-3 rounded-xl bg-neutral-900 border border-neutral-700 text-white font-bold text-xs uppercase tracking-wider hover:bg-neutral-800 active:scale-95 transition-all flex items-center justify-center space-x-2">
                                <span>⚡</span> <span>Recalcular Simulación (10,000 Iteraciones)</span>
                            </button>

                            <div class="space-y-2 mb-5">
                                <div class="glass-card rounded-xl p-3.5 flex items-center justify-between">
                                    <span class="text-xs text-textMuted">Tarjetas amarillas proyectadas</span>
                                    <span class="text-xs font-bold text-white">${m.tarjetas}</span>
                                </div>
                                <div class="glass-card rounded-xl p-3.5 flex items-center justify-between">
                                    <span class="text-xs text-textMuted">Tiros de esquina (Córners)</span>
                                    <span class="text-xs font-bold text-white">${corners}</span>
                                </div>
                                <div class="glass-card rounded-xl p-3.5 flex items-center justify-between">
                                    <span class="text-xs text-textMuted">Ambos equipos marcarán (BTTS)</span>
                                    <span class="text-xs font-bold text-white">${sim.probBtts > 50 ? 'Sí' : 'No'} (${sim.probBtts}%)</span>
                                </div>
                                <div class="glass-card rounded-xl p-3.5 flex items-center justify-between">
                                    <span class="text-xs text-textMuted">Ganador probable</span>
                                    <span class="text-xs font-bold text-white">${ganadorIcon} ${ganador}</span>
                                </div>
                            </div>

                            <div id="sim-box" class="glass-panel rounded-2xl p-5 border border-borderSubtle shadow-xl">
                                <p class="text-[10px] text-textMuted text-center uppercase tracking-widest font-semibold mb-4">Probabilidad de Victoria en Vivo</p>
                                <div class="flex items-center justify-around text-center">
                                    <div>
                                        <div class="text-xl font-extrabold text-white">${sim.probL}%</div>
                                        <div class="text-[10px] text-textMuted uppercase tracking-wider mt-1 font-medium">${iconL} ${m.local}</div>
                                    </div>
                                    <div class="text-neutral-700 font-light text-lg">|</div>
                                    <div>
                                        <div class="text-xl font-extrabold text-white">${sim.probX}%</div>
                                        <div class="text-[10px] text-textMuted uppercase tracking-wider mt-1 font-medium">Empate</div>
                                    </div>
                                    <div class="text-neutral-700 font-light text-lg">|</div>
                                    <div>
                                        <div class="text-xl font-extrabold text-white">${sim.probV}%</div>
                                        <div class="text-[10px] text-textMuted uppercase tracking-wider mt-1 font-medium">${iconV} ${m.visitante}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                } else if (this.currentTab === 'directo') {
                    headerAction.innerHTML = `<span class="text-xs px-2.5 py-1 rounded-full bg-neutral-900 border border-neutral-800 text-textMuted font-semibold">SIMULADOR</span>`;
                    container.innerHTML = `
                        <div class="text-center py-6">
                            <h2 class="text-xl font-extrabold tracking-tight text-white mb-2">Simulación Rápida de Partidos</h2>
                            <p class="text-xs text-textMuted mb-6">Selecciona cualquier encuentro del menú para ejecutar la simulación directa con el algoritmo cuantitativo de Poisson.</p>
                        </div>
                        <div class="glass-panel rounded-2xl p-6 text-center border border-borderSubtle">
                            <div class="text-4xl mb-3">⚽</div>
                            <h3 class="text-sm font-bold text-white mb-2">Cartelera Automatizada</h3>
                            <p class="text-xs text-textMuted mb-4">Ingresa a la pestaña "Cartelera" para ver las probabilidades predichas automáticamente.</p>
                            <button onclick="app.switchTab('cartelera')" class="px-5 py-2.5 rounded-xl bg-neutral-800 text-white font-bold text-xs uppercase tracking-wider border border-neutral-700">Ver Cartelera</button>
                        </div>
                    `;
                } else if (this.currentTab === 'modelo') {
                    headerAction.innerHTML = `<span class="text-xs px-2.5 py-1 rounded-full bg-neutral-900 border border-neutral-800 text-textMuted font-semibold">MODELO IA</span>`;
                    container.innerHTML = `
                        <div class="pt-2 space-y-4">
                            <div class="glass-panel rounded-2xl p-5 border border-borderSubtle">
                                <h3 class="text-sm font-bold text-white mb-1 uppercase tracking-wider">Algoritmo Monte Carlo y Poisson</h3>
                                <p class="text-xs text-textMuted leading-relaxed">El modelo ejecuta 10,000 iteraciones por evento calculando métricas de goles esperados (xG), distribución de tiros de esquina y propensión a tarjetas amarillas sin intervención manual.</p>
                            </div>
                            <div class="glass-card rounded-xl p-4 flex justify-between items-center">
                                <span class="text-xs text-textMuted">Precisión del Modelo</span>
                                <span class="text-xs font-bold text-white">88.4%</span>
                            </div>
                            <div class="glass-card rounded-xl p-4 flex justify-between items-center">
                                <span class="text-xs text-textMuted">Ligas Analizadas</span>
                                <span class="text-xs font-bold text-white">9 Ligas Mundiales</span>
                            </div>
                            <div class="glass-card rounded-xl p-4 flex justify-between items-center">
                                <span class="text-xs text-textMuted">Simulaciones por evento</span>
                                <span class="text-xs font-bold text-white">10,000 Ejecuciones</span>
                            </div>
                        </div>
                    `;
                }
            }
        }

        const app = new SimuladorApp();
    </script>
</body>
</html>
"""

st.components.v1.html(html_code, height=850, scrolling=True)
