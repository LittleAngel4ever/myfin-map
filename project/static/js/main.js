const translations = {
ru: {
mainTitle: 'Корпорация кота "Окак"',
mapTitle: 'Здесь будет карта',
corpName: 'Корпорация кота "Окак"',
langBtn: 'English',
selectCurrency: 'Валюта ▾',
aboutUs: 'О нас',
contacts: 'Контакты',
support: 'Поддержка',
parsing: 'Парсинг данных ожидайте...'
},
en: {
mainTitle: 'Okak Cat Corporation',
mapTitle: 'Map will be here',
corpName: 'Okak Cat Corporation',
langBtn: 'Русский',
selectCurrency: 'Currency ▾',
aboutUs: 'About Us',
contacts: 'Contacts',
support: 'Support',
parsing: 'Parsing data, please wait...'
}
};
let currentLang = localStorage.getItem('lang') || 'ru';
let isDarkTheme = localStorage.getItem('theme') !== 'light';
let currentCurrency = localStorage.getItem('currency') || 'USD';
let isParsingInProgress = false;
if (!isDarkTheme) {
document.body.classList.add('light-theme');
}
function applyTheme() {
if (isDarkTheme) {
document.body.classList.remove('light-theme');
} else {
document.body.classList.add('light-theme');
}
const themeBtn = document.getElementById('theme-btn');
if (themeBtn) {
themeBtn.textContent = isDarkTheme ? '🌙' : '☀️';
}
}
function updateLanguage() {
const elements = document.querySelectorAll('[data-translate]');
elements.forEach(element => {
const key = element.getAttribute('data-translate');
if (translations[currentLang][key]) {
element.textContent = translations[currentLang][key];
}
});
const langBtn = document.getElementById('lang-btn');
if (langBtn) {
    langBtn.textContent = translations[currentLang].langBtn;
}
}
function showParsingIndicator() {
const mapSection = document.querySelector('.map-section');
if (!mapSection) return;
mapSection.innerHTML = `
     <div style= "display: flex; justify-content: center; align-items: center; height: 400px; flex-direction: column; " >
         <div style= "font-size: 18px; color: #666; margin-bottom: 20px; " >
            ${translations[currentLang].parsing}
         </div >
         <div style= "border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; " > </div >
         <style >
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
         </style >
     </div >
`;
}
function loadMap(currency) {
const mapSection = document.querySelector('.map-section');
if (!mapSection) return;
mapSection.innerHTML = '<p style="text-align:center; padding:20px;">Загрузка карты...</p>';

fetch('/api/map', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({ currency: currency })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        mapSection.innerHTML = '';
        const iframe = document.createElement('iframe');
        iframe.style.width = '100%';
        iframe.style.height = '100%';
        iframe.style.border = 'none';
        iframe.style.borderRadius = '10px';
        mapSection.appendChild(iframe);

        const doc = iframe.contentDocument || iframe.contentWindow.document;
        doc.open();
        doc.write(data.map_html);
        doc.close();

        currentCurrency = currency;
        localStorage.setItem('currency', currency);
        isParsingInProgress = false;
    } else {
        showParsingIndicator();
        startParsing(currency);
    }
})
.catch(error => {
    console.error('Ошибка при загрузке карты:', error);
    showParsingIndicator();
    startParsing(currency);
});
}
function startParsing(currency) {
if (isParsingInProgress) return;
isParsingInProgress = true;
fetch('/api/parse', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({ currency: currency })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        pollForMapReady(currency);
    } else {
        const mapSection = document.querySelector('.map-section');
        if (mapSection) {
            mapSection.innerHTML = `<p style='color:red; text-align:center;'>Ошибка парсинга: ${data.error}</p>`;
        }
        isParsingInProgress = false;
    }
})
.catch(error => {
    console.error('Ошибка при запуске парсинга:', error);
    const mapSection = document.querySelector('.map-section');
    if (mapSection) {
        mapSection.innerHTML = '<p style="color:red; text-align:center;">Не удалось запустить парсинг. Проверьте соединение.</p>';
    }
    isParsingInProgress = false;
});
}
function pollForMapReady(currency, attempts = 0, maxAttempts = 120) {
if (attempts >= maxAttempts) {
const mapSection = document.querySelector('.map-section');
if (mapSection) {
mapSection.innerHTML = '<p style="color:red; text-align:center;">Парсинг занял слишком долго. Попробуйте позже.</p>';
}
isParsingInProgress = false;
return;
}
setTimeout(() => {
    fetch('/api/map', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ currency: currency })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const mapSection = document.querySelector('.map-section');
            if (mapSection) {
                mapSection.innerHTML = '';
                const iframe = document.createElement('iframe');
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.border = 'none';
                iframe.style.borderRadius = '10px';
                mapSection.appendChild(iframe);

                const doc = iframe.contentDocument || iframe.contentWindow.document;
                doc.open();
                doc.write(data.map_html);
                doc.close();

                currentCurrency = currency;
                localStorage.setItem('currency', currency);
            }
            isParsingInProgress = false;
        } else {
            pollForMapReady(currency, attempts + 1, maxAttempts);
        }
    })
    .catch(error => {
        console.error('Ошибка при проверке карты:', error);
        pollForMapReady(currency, attempts + 1, maxAttempts);
    });
}, 2000);
}
function checkAndInitializeMap() {
const mapSection = document.querySelector('.map-section');
if (!mapSection) return;
const mapContent = mapSection.innerHTML.trim();

if (!mapContent || mapContent.includes('Ошибка') || mapContent.includes('Error')) {
    showParsingIndicator();
    startParsing(currentCurrency);
}
}
document.addEventListener('DOMContentLoaded', () => {
applyTheme();
updateLanguage();
checkAndInitializeMap();
const themeBtn = document.getElementById('theme-btn');
if (themeBtn) {
    themeBtn.addEventListener('click', () => {
        isDarkTheme = !isDarkTheme;
        localStorage.setItem('theme', isDarkTheme ? 'dark' : 'light');
        applyTheme();
    });
}

const langBtn = document.getElementById('lang-btn');
if (langBtn) {
    langBtn.addEventListener('click', () => {
        currentLang = currentLang === 'ru' ? 'en' : 'ru';
        localStorage.setItem('lang', currentLang);
        updateLanguage();
    });
}

const dropdown = document.querySelector('.dropdown');
const dropdownBtn = document.querySelector('.dropdown-btn');

if (dropdownBtn) {
    dropdownBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('show');
    });
}

document.addEventListener('click', (e) => {
    if (dropdown && !dropdown.contains(e.target)) {
        dropdown.classList.remove('show');
    }
});

const currencyLinks = document.querySelectorAll('.dropdown-content a');
currencyLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const currency = link.getAttribute('data-currency');
        const currencyText = link.textContent.trim();
        
        if (dropdownBtn) {
            dropdownBtn.textContent = currencyText;
        }
        
        dropdown.classList.remove('show');
        
        loadMap(currency);
    });
});
});