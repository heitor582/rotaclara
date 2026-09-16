'use strict';
const toast=document.getElementById('toast');
let timer;
document.querySelectorAll('.copy-code').forEach(button=>button.addEventListener('click',async()=>{
 const code=button.closest('.source').querySelector('code');
 try{await navigator.clipboard.writeText(code.textContent);toast.textContent='Código PlantUML copiado.';toast.hidden=false;clearTimeout(timer);timer=setTimeout(()=>toast.hidden=true,3000);}
 catch{toast.textContent='Selecione o código abaixo e copie com Ctrl+C ou ⌘C.';toast.hidden=false;}
}));
document.querySelectorAll('.diagram-image img').forEach(img=>{
 const fail=()=>{img.closest('.diagram-image').hidden=true;img.closest('.diagram-card').querySelector('.image-error').hidden=false;};
 img.addEventListener('error',fail);
 if(img.complete&&!img.naturalWidth&&img.getAttribute('loading')!=='lazy')fail();
});
