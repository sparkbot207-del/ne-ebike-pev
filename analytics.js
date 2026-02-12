(function(){
var E='https://adjustment-fundamentals-notification-copyrights.trycloudflare.com/api/t';
var s=sessionStorage.getItem('_sid')||(sessionStorage._sid='s'+Date.now(),sessionStorage._sid);
function t(type,el){new Image().src=E+'?s='+s+'&t='+type+'&p='+encodeURIComponent(location.pathname)+(el?'&e='+encodeURIComponent(el):'')+'&_='+Date.now();}
t('pageview');
document.addEventListener('click',function(e){var a=e.target.closest('a,button');if(a)t('click',a.innerText?.slice(0,30)||a.tagName);});
})();
