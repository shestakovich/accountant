let cache = {};


const input_row_sample = document.querySelector('.enter-sale__row-wrapper').firstElementChild.cloneNode(true);
setter_events_listener(document.querySelector('.enter-sale__row-wrapper .enter-sale__row'));
dropdown_setter(document.querySelector('._client'), async (q) => {
    let response = await fetch(`/api/clients_options/?q=${q}`);
    let data = await response.json();
    console.log(data['clients'])
    return data['clients']
});
document.querySelector("._sale_form").addEventListener('submit', event => {
    document.querySelectorAll('._sale_form .enter-sale__row-wrapper .enter-sale__row').forEach((el, key)=>{
        el.querySelectorAll('input').forEach(input_el=>{
            input_el.name = [input_el.name.split('_')[0], key].join('_')
            if (input_el.name.startsWith('price')){
                input_el.value = input_el.value ? parseFloat(input_el.value).toString() : ''
            }
            if (input_el.name.startsWith('duration')){
                input_el.value = input_el.value ? input_el.value + ':00' : ''
            }
        })

    })
    // event.preventDefault()
})


function dropdown_setter(el, download_list, button_click_callback = null) {
    const drop_item_sample = el.querySelector('.dropdown__list button').cloneNode(true);
    el.querySelector('.dropdown__list').innerHTML = '';

    let drop_list = el.querySelector('.dropdown__list');
    let drop_input = el.querySelector('.dropdown input');


    drop_input.addEventListener('input', async function (event) {
        drop_list.innerHTML = '';
        if (drop_input.value !== '') {
            let l = await download_list(drop_input.value);
            for (let line of l) {
                // создание строки
                let n = drop_item_sample.cloneNode(true);
                for (let key in line) {  // заполнение данными
                    if (Array.isArray(line[key])) {

                        for (let ar_line of line[key]) {
                            let el = Array.from(n.querySelectorAll('._' + key)).pop();
                            el.innerText = ar_line;
                            let new_el = el.cloneNode();
                            new_el.innerText = ar_line;
                            el.after(new_el)
                        }
                        Array.from(n.querySelectorAll('._' + key)).pop().remove()
                    } else {
                        n.querySelector('._' + key).innerText = line[key]
                    }
                }
                drop_list.append(n);

                // Установка клика
                n.addEventListener('mousedown', (ev) => {
                    if (ev.button !== 0) { // Only right click
                        return
                    }

                    drop_input.value = n.querySelector('._main').innerText;

                    if (button_click_callback !== null) {
                        button_click_callback(drop_input);
                    }
                })

            }
        }

    });
    drop_input.addEventListener('focusin', function (event) {
        drop_list.style.display = 'block'
    });

    drop_input.addEventListener('focusout', function (event) {
        drop_list.style.display = 'none'
    });

}


async function download_services_list(q) {
    let response = await fetch(`/api/service_options/?q=${q}`);
    let data = await response.json();
    return data['services']
}


function row_validator(row) {

    let service_input = row.querySelector('._service-input');
    let price_input = row.querySelector('._price-input');

    if (service_input.value === '' && !row_is_empty(row)) {
        service_input.classList.add('input__error')

    } else {
        service_input.classList.remove('input__error')

    }

    if (price_input.value === '' && !row_is_empty(row)) {
        price_input.classList.add('input__error')
    } else {

        price_input.classList.remove('input__error')
    }


}

function control_default_value_in_row(row) {
    if (row_is_empty(row)) {
        row.querySelector('._count-input').placeholder = 'Кол-во'
    } else {
        row.querySelector('._count-input').placeholder = '1'

    }
}

function setter_events_listener(row) {
    // Установка функций для каждой новой строки с вводом сервиса

    dropdown_setter(row, download_services_list, (drop_input) => {
        row.querySelector('.enter-sale__new-row').style.display = 'none';

        drop_input.addEventListener('blur', () => {
            row.querySelector('._price-input').focus()
        }, {once: true});
    });
    let service_input = row.querySelector('._service-input');

    service_input.addEventListener('input', async (ev) => {
        if (service_input.value !== '') {
            let data = await download_data_tip(service_input.value);
            if (data !== null) {
                row.querySelector('.enter-sale__new-row').style.display = 'none';
                show_tip(data)
            } else {
                row.querySelector('.enter-sale__new-row').style.display = 'block'
            }
        }
    });

    row.querySelector('._duration-input').addEventListener('input', (ev) => {
        let duration = ev.target;
        let value = duration.value;
        if (value !== '') {
            let digits = parseInt('0' + value.replace(/\D+/g, '')).toString().slice(0, 4);
            if (parseInt(digits) === 0) {
                duration.value = ''
            } else {
                let prepare_digits = '0'.repeat(4 - digits.length) + digits;
                duration.value = prepare_digits.slice(0, 2) + ':' + prepare_digits.slice(2, 4);
            }

        }

    });
    row.querySelector('._duration-input').addEventListener('focus', (ev) => {
        ev.target.select()
    });
    row.querySelector('._duration-input').addEventListener('blur', (ev) => {
        if (ev.target.value !== '') {
            if (parseInt(ev.target.value.slice(3, 5)) > 59) {
                ev.target.value = ev.target.value.slice(0, 3) + '59';
            }
        }

    });

    row.querySelector('._price-input').addEventListener('focus', (ev) => {
        ev.target.select()
    });


    row.querySelector('._price-input').addEventListener('input', (ev) => {
        let price = ev.target;
        if (!isNaN(parseInt(price.value))) {
            price.value = parseInt(price.value) + ' руб';
            price.selectionStart = price.value.length - 4;
            price.selectionEnd = price.value.length - 4;
        } else {
            price.value = ''
        }
    });


    row.querySelectorAll('input').forEach(function (input) {
        input.addEventListener('focusin', async () => {
            let service = row.querySelector('._service-input').value;
            if (service !== '') {
                let data = await download_data_tip(service);
                if (data !== null) {
                    show_tip(data);
                }
            }

            row.querySelectorAll('input').forEach(function (el) {
                el.classList.add('input__last-focus')
            })
        });
        input.addEventListener('focusout', () => {
            control_default_value_in_row(row);
            close_tip();

            if (!row_is_empty(row)) {
                row.querySelectorAll('input').forEach(function (el) {
                    el.classList.remove('input__last-focus')
                })
            }

        });

        input.addEventListener('blur', () => {
            control_last_row();
            row_validator(row);
        })
    });
    row.querySelector('.row__close-button').addEventListener('click', (ev) => {
        row.remove()
    });
}


async function download_data_tip(service) {
    let data = cache[service];
    if (!data) {
        // download
        let response = await fetch(`/api/service_tip/?q=${service}`);
        data = await response.json();
        cache[service] = data;
    }
    if (data['error']) {
        return null
    }
    return data
}

async function downloader(url, cacheable = true) {
    let data = cache[url];
    if (!data) {
        // download
        let response = await fetch(url);
        data = await response.json();
        if (cacheable)
            cache[url] = data;
    }
    if (data['error']) {
        throw Error(data['error'])
    }
    return data
}


function row_is_empty(row) { // Пустая если нет цены и услуги
    return row.querySelector('._service-input').value === '' && row.querySelector('._price-input').value === '';

}

function control_last_row() {
    const rows = document.querySelector('.enter-sale__row-wrapper');
    let last_row = rows.lastElementChild;
    if (!row_is_empty(last_row)) {
        last_row.querySelector('.row__close-button').style.display = 'block';
        last_row.querySelector('.enter-sale__mul').style.display = 'block';
        let new_row = input_row_sample.cloneNode(true);
        rows.append(new_row);
        setter_events_listener(new_row);
    }
    let prev_row = last_row.previousElementSibling;
    if (prev_row && row_is_empty(prev_row)) {
        prev_row.remove()
    }

}

const tip = document.querySelector('.tip');
tip.querySelector('.tip__close-button').addEventListener('click', close_tip);

function show_tip(data) {
    tip.querySelector('.tip__title').innerText = data['title'];
    tip.querySelectorAll('.tip__prices')[0].innerText = `Средняя цена: ${data['avg_price']} руб`;
    tip.querySelectorAll('.tip__prices')[1].innerText = `Минимальная цена: ${data['min_price']} руб`;

    chart_handler.data.datasets[0].data = data['chart_data'];
    chart_handler.update();

    tip.classList.remove('tip_hidden');
}

function close_tip() {
    tip.classList.add('tip_hidden');
}


const ctx = document.getElementById('tip_chart').getContext('2d');

const chart_handler = new Chart(ctx, {
    type: 'line',
    data: {
        datasets: [{
            backgroundColor: '#FFFFFF',
            borderColor: '#FFFFFF',
            fill: false,
            data: []
        }]
    },
    options: {
        legend: {
            display: false
        },
        responsive: true,
        scales: {

            xAxes: [{
                type: 'time',
                time: {
                    displayFormats: {
                        day: 'DD.MM',
                        hour: 'HH:mm',
                        minute: 'HH:mm',
                        second: 'HH:mm:ss',
                    },
                },

                display: true,

                ticks: {
                    fontColor: '#F0F0F0',
                }
            }],
            yAxes: [{
                display: true,
                ticks: {
                    fontColor: '#F0F0F0',
                }
            }]
        }
    }
});


