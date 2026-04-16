document.addEventListener('DOMContentLoaded', function() {
    const dropLocal = document.getElementById('dropLocal');
    const dropSetor = document.getElementById('dropSetor');
    
    if (dropLocal && dropSetor) {
        const opcoesOriginais = Array.from(dropSetor.options);

        function filtrarSetores() {
            const cantina = dropLocal.value;
            dropSetor.innerHTML = ''; 
            
            opcoesOriginais.forEach(opt => {
                const txt = opt.text; // Pegamos o texto exato
                let mostrar = false;

                if (opt.value === '') {
                    // Mantém a opção "Selecione..." sempre visível
                    mostrar = true; 
                } 
                else if (cantina === 'SEDE') {
                    // SETORES DA SEDE
                    if (txt === 'Colaborador sede' || 
                        txt === 'Corporativo sede' || 
                        txt === 'Terceiros Fazenda') {
                        mostrar = true;
                    }
                } 
                else if (cantina === 'SECADOR') {
                    // SETORES DO SECADOR
                    if (txt === 'Colaborador secador' || 
                        txt === 'Colaborador algodoeira' || 
                        txt === 'Terceirizado algodoeira' || 
                        txt === 'Safrista algodoeira' || 
                        txt === 'Corporativo' || 
                        txt === 'Terceiros Fazenda') {
                        mostrar = true;
                    }
                }

                // Se passou no teste, injeta no HTML
                if (mostrar) { 
                    dropSetor.appendChild(opt); 
                }
            });
        }

        dropLocal.addEventListener('change', filtrarSetores);
        filtrarSetores(); 
    }
});