(function(){
const E='https://adjustment-fundamentals-notification-copyrights.trycloudflare.com/api/track';
function sid(){let i=sessionStorage.getItem('_sid');if(!i){i='s'+Date.now();sessionStorage.setItem('_sid',i)}return i}
function send(type,data){
  fetch(E,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sid(),event_type:type,page:location.pathname,element:data?.el||null,metadata:data?.meta||{}}),mode:'cors'}).catch(function(){});
}
send('pageview',{meta:{ref:document.referrer,title:document.title}});
document.addEventListener('click',function(e){var t=e.target.closest('a,button');if(t)send('click',{el:t.innerText?.slice(0,50)||t.tagName,meta:{href:t.href||''}});});
})();
