// ==========================================
// FUNÇÕES GLOBAIS (Acessíveis pelo HTML)
// ==========================================

function mudarPagina(numeroDaPagina) {
    const url = new URL(window.location.href);
    url.searchParams.set('page', numeroDaPagina);
    window.location.href = url.toString();
}

function irParaPaginaDigitada() {
    const input = document.getElementById('input-pagina');
    let num = parseInt(input.value);
    const max = parseInt(input.max);
    const min = parseInt(input.min);

    if (num >= min && num <= max) {
        mudarPagina(num);
    } else {
        alert('Página inválida. Digite um número entre ' + min + ' e ' + max);
        const activePageElement = document.querySelector('.page-active');
        if (activePageElement) {
            input.value = activePageElement.innerText.match(/\d+/)[0];
        }
    }
}

function inicializarGraficosDashboard(dados) {
    const canvasAcumulado = document.getElementById('chartAcumuladoPeriodo');
    const canvas3Meses = document.getElementById('chart3Meses');
    const canvasCompleto = document.getElementById('graficoComparativoBarras');

    if (!canvasAcumulado || !canvasCompleto) return;

    // --- 1. GRÁFICO ACUMULADO ---
    new Chart(canvasAcumulado.getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Total Acumulado Histórico'],
            datasets: [
                { label: 'Colaboradores', data: [dados.totalColabPeriodo], backgroundColor: '#10b981',
                    borderRadius: 5, borderWidth: 0 },
                { label: 'Terceirizados', data: [dados.totalTercPeriodo], backgroundColor: '#a855f7',
                    borderRadius: 5, borderWidth: 0 }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { color: '#94a3b8', font: { weight: '600' } } },
                tooltip: { callbacks: { label: function(c) { return c.dataset.label + ': R$ ' +
                            (c.raw || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2}); } } }
            },
            scales: {
                y: { ticks: { color: '#94a3b8', callback: function(v) { return 'R$ ' +
                            v.toLocaleString('pt-BR', {minimumFractionDigits: 0}); } },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                x: { ticks: { color: '#94a3b8' }, grid: { display: false } }
            }
        }
    });

    // --- FÁBRICA DE PLUGIN DE TEXTO NAS BARRAS ---
    function criarPluginTexto(qtdsColabArray, qtdsTercArray, idPlugin) {
        return {
            id: idPlugin,
            afterDatasetsDraw(chart) {
                const ctx = chart.ctx;
                ctx.save();
                ctx.font = 'bold 11px sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';
                chart.data.datasets.forEach((dataset, i) => {
                    const meta = chart.getDatasetMeta(i);
                    meta.data.forEach((bar, index) => {
                        const qtd = i === 0 ? qtdsColabArray[index] : qtdsTercArray[index];
                        if (qtd > 0) {
                            ctx.fillStyle = '#e2e8f0';
                            ctx.fillText(qtd + ' un', bar.x, bar.y - 5);
                        }
                    });
                });
                ctx.restore();
            }
        };
    }

    function gerarOpcoesBase() {
        return {
            responsive: true, maintainAspectRatio: false, layout: { padding: { top: 15 } },
            plugins: {
                legend: { position: 'top', labels: { color: '#94a3b8', font: { weight: '600' }, padding: 15 } },
                tooltip: { callbacks: {} } // Caixinha pré-criada para evitar erros no JavaScript
            },
            scales: {
                y: { grace: '20%', ticks: { color: '#94a3b8', callback: function(v)
                        { return 'R$ ' + v.toLocaleString('pt-BR', {minimumFractionDigits: 0}); } },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                x: { ticks: { color: '#94a3b8' }, grid: { display: false } }
            }
        };
    }

    if (canvas3Meses) {
        const labels3M = dados.mesesLabels.slice(-3);
        const dColab3M = dados.dadosColaborador.slice(-3);
        const dTerc3M = dados.dadosTerceirizado.slice(-3);
        const qColab3M = dados.qtdsColab.slice(-3);
        const qTerc3M = dados.qtdsTerc.slice(-3);

        const config3M = gerarOpcoesBase();
        config3M.plugins.tooltip.callbacks.label = function(c) {
            let q = c.datasetIndex === 0 ? qColab3M[c.dataIndex] : qTerc3M[c.dataIndex];
            return `${c.dataset.label}: R$ ${(c.raw || 0).toLocaleString('pt-BR', 
                {minimumFractionDigits: 2})} (${q} un)`;
        };

        new Chart(canvas3Meses.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels3M,
                datasets: [
                    { label: 'Colaboradores', data: dColab3M, backgroundColor: '#10b981',
                        borderRadius: 4, borderWidth: 0 },
                    { label: 'Terceirizados', data: dTerc3M, backgroundColor: '#a855f7',
                        borderRadius: 4, borderWidth: 0 }
                ]
            },
            plugins: [criarPluginTexto(qColab3M, qTerc3M, 'pluginTexto3M')],
            options: config3M
        });
    }

    const configCompleto = gerarOpcoesBase();
    configCompleto.plugins.tooltip.callbacks.label = function(c) {
        let q = c.datasetIndex === 0 ? dados.qtdsColab[c.dataIndex] : dados.qtdsTerc[c.dataIndex];
        return `${c.dataset.label}: R$ ${(c.raw || 0).toLocaleString('pt-BR', 
            {minimumFractionDigits: 2})} (${q} un)`;
    };

    new Chart(canvasCompleto.getContext('2d'), {
        type: 'bar',
        data: {
            labels: dados.mesesLabels,
            datasets: [
                { label: 'Colaboradores', data: dados.dadosColaborador,
                    backgroundColor: '#10b981', borderRadius: 4, borderWidth: 0 },
                { label: 'Terceirizados', data: dados.dadosTerceirizado,
                    backgroundColor: '#a855f7', borderRadius: 4, borderWidth: 0 }
            ]
        },
        plugins: [criarPluginTexto(dados.qtdsColab, dados.qtdsTerc, 'pluginTextoCompleto')],
        options: configCompleto
    });
}

document.addEventListener('DOMContentLoaded', function() {

    document.querySelectorAll('.page-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            mudarPagina(page);
        });
    });

    const btnTema = document.getElementById("btn-tema");
    const iconeTema = document.getElementById("icone-tema");
    const htmlTag = document.documentElement;

    if (localStorage.getItem('tema-refeicoes') === 'claro') {
        if(iconeTema) iconeTema.classList.replace('fa-sun', 'fa-moon');
    }

    if (btnTema) {
        btnTema.addEventListener("click", function() {
            htmlTag.classList.toggle('theme-light');
            if (htmlTag.classList.contains('theme-light')) {
                localStorage.setItem('tema-refeicoes', 'claro');
                if(iconeTema) iconeTema.classList.replace('fa-sun', 'fa-moon');
            } else {
                localStorage.setItem('tema-refeicoes', 'escuro');
                if(iconeTema) iconeTema.classList.replace('fa-moon', 'fa-sun');
            }
        });
    }

    const selectFazenda = document.querySelector('select[name="fazenda"]');
    const selectCantina = document.querySelector('select[name="local"]');

    if (selectFazenda && selectCantina) {
        const todasOpcoesCantina = Array.from(selectCantina.options);

        function atualizarCantinas(evento) {
            const fazendaSelecionada = selectFazenda.options[selectFazenda.selectedIndex].text;
            const valorAtualCantina = selectCantina.value;

            selectCantina.innerHTML = '';
            const opcoesParaAdicionar = [];

            todasOpcoesCantina.forEach(opcao => {
                const nomeCantina = opcao.text;
                const isOpcaoTodas = opcao.value === '';

                if (fazendaSelecionada === 'Todas as Fazendas') {
                    opcoesParaAdicionar.push(opcao);
                }
                else if (fazendaSelecionada.includes('Independ')) {
                    if (isOpcaoTodas || nomeCantina.includes('Sede') || nomeCantina.includes('Secador')) {
                        opcoesParaAdicionar.push(opcao);
                    }
                }
                else if (fazendaSelecionada.includes('BC')) {
                    if (!isOpcaoTodas && nomeCantina.includes('BC')) opcoesParaAdicionar.push(opcao);
                }
                else if (fazendaSelecionada.includes('Matão')) {
                    if (!isOpcaoTodas && nomeCantina.includes('Matão')) opcoesParaAdicionar.push(opcao);
                }
                else if (fazendaSelecionada.includes('Lagoa')) {
                    if (!isOpcaoTodas && nomeCantina.includes('Lagoa')) opcoesParaAdicionar.push(opcao);
                }
            });

            opcoesParaAdicionar.forEach(opcao => {
                selectCantina.appendChild(opcao.cloneNode(true));
            });

            if (selectCantina.options.length === 1) {
                selectCantina.style.pointerEvents = 'none';
                selectCantina.style.appearance = 'none';
                selectCantina.style.backgroundImage = 'none';
                selectCantina.style.opacity = '0.85';
            } else {
                selectCantina.style.pointerEvents = 'auto';
                selectCantina.style.removeProperty('appearance');
                selectCantina.style.removeProperty('background-image');
                selectCantina.style.removeProperty('opacity');
            }

            if (evento && fazendaSelecionada === 'Todas as Fazendas') {
                selectCantina.value = '';
            } else {
                const opcaoAindaExiste = Array.from(selectCantina.
                    options).some(opt => opt.value === valorAtualCantina);
                selectCantina.value = opcaoAindaExiste ? valorAtualCantina :
                    (selectCantina.options.length > 0 ? selectCantina.options[0].value : '');
            }
        }

        selectFazenda.addEventListener('change', atualizarCantinas);
        atualizarCantinas(null);
    }

    // 4. Filtro Inteligente Cantina -> Setor (Novo Lançamento)
    const campoCantina = document.getElementById("dropLocal");
    const campoSetor = document.getElementById("dropSetor");

    if (campoCantina && campoSetor) {
        const backupDados = Array.from(campoSetor.options).map(opt => ({
            value: opt.value,
            text: opt.text
        }));

        function filtrarSetores() {
            const cantinaEscolhida = campoCantina.value;
            const valorSetorAnterior = campoSetor.value;

            campoSetor.innerHTML = "";

            if (cantinaEscolhida !== 'SEDE' && cantinaEscolhida !== 'SECADOR') {
                backupDados.forEach(dado => {
                    campoSetor.add(new Option(dado.text, dado.value));
                });
                campoSetor.value = valorSetorAnterior;
                return;
            }

            const setoresSede = ['colaborador sede', 'terceiros fazenda'];
            const setoresSecador = [
                'colaborador secador', 'safrista secador', 'colaborador algodoeira',
                'terceirizado algodoeira', 'safrista algodoeira', 'corporativo', 'colaborador escritorio'
            ];

            backupDados.forEach(dado => {
                const valorMinusculo = dado.value.toLowerCase();

                if (!dado.value) {
                    campoSetor.add(new Option(dado.text, dado.value));
                    return;
                }

                let mostrar = false;
                if (cantinaEscolhida === 'SEDE' && setoresSede.includes(valorMinusculo)) {
                    mostrar = true;
                } else if (cantinaEscolhida === 'SECADOR' && setoresSecador.includes(valorMinusculo)) {
                    mostrar = true;
                }

                if (mostrar) {
                    campoSetor.add(new Option(dado.text, dado.value));
                }
            });

            campoSetor.value = valorSetorAnterior;
        }

        campoCantina.addEventListener("change", filtrarSetores);
        filtrarSetores();
    }
});