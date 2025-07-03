function getOtherFields(inputId) {

    const input = document.getElementById(inputId) //Обращаюсь к странице с поиском указанного в параметрах айди
    if (!input) return;

    input.addEventListener('input', () => { //Создаю слушателя на ввод данных
        const query = input.value //Создаю переменную считывающую пользовательский ввод

        if (query.length < 2) return; //Если пользовательский ввод меньше чем 2 символа, тогда ничего не выводим

        fetch(`/search_employee?q=${encodeURIComponent(query)}`)
        .then(res=>res.json())
        .then(data=> {

            const existingList = input.parentNode.querySelector(".autocomplete-list");
            if (existingList) existingList.remove();

            const list = document.createElement("ul");
            list.className = "autocomplete-list";
            list.style.position = "absolute";
            list.style.zIndex = "1000";
            list.style.backgroundColor = "white";
            list.style.border = "1px solid #ccc";
            list.style.listStyle = "none";
            list.style.padding = "0";
            list.style.marginTop = "0";

            data.forEach(item => {

                const li = document.createElement("li");
                li.textContent = item['full_name'];
                li.style.padding = "5px 10px";
                li.style.cursor = "pointer";

                li.addEventListener("click", () => {

                    const staff_number = document.getElementById('register-page-staff-number')
                    const position = document.getElementById('register-page-position')
                    const department = document.getElementById('register-page-department')
                    const email = document.getElementById('register-page-email')

                    input.value = item['full_name'];
                    staff_number.value = item['staff_number']
                    position.value = item['department']
                    department.value = item['position']
                    email.value = item['email']
                    list.remove();
                });

                list.appendChild(li);
            });

            input.parentNode.appendChild(list);
        });
    })

}
// Дроплист для полей "Куратор" и "Спикер"
function initAutocomplete(inputId, options = {}) {
    const input = document.getElementById(inputId);
    if (!input) return;

    const {
        url = "/search_employees",
        minChars = 2,
        labelField = "label",
        valueField = "value",
        hiddenInputId = null,  // если нужен табельный номер отдельно
    } = options;

    let timeout = null;
    input.addEventListener("input", () => {
        clearTimeout(timeout);
        const query = input.value;

        if (query.length < minChars) return;

        timeout = setTimeout(() => {
            fetch(`${url}?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    const existingList = input.parentNode.querySelector(".autocomplete-list");
                    if (existingList) existingList.remove();

                    const list = document.createElement("ul");
                    list.className = "autocomplete-list";
                    list.style.position = "absolute";
                    list.style.zIndex = "1000";
                    list.style.backgroundColor = "white";
                    list.style.border = "1px solid #ccc";
                    list.style.listStyle = "none";
                    list.style.padding = "0";
                    list.style.marginTop = "0";

                    data.forEach(item => {
                        const li = document.createElement("li");
                        li.textContent = item[labelField];
                        li.style.padding = "5px 10px";
                        li.style.cursor = "pointer";

                        li.addEventListener("click", () => {
                            input.value = item[valueField];
                            if (hiddenInputId) {
                                const hiddenInput = document.getElementById(hiddenInputId);
                                if (hiddenInput) {
                                    hiddenInput.value = item[valueField];
                                }
                            }
                            list.remove();
                        });

                        list.appendChild(li);
                    });

                    input.parentNode.appendChild(list);
                });
        }, 300);
    });

    document.addEventListener("click", (e) => {
        const list = input.parentNode.querySelector(".autocomplete-list");
        if (list && !list.contains(e.target) && e.target !== input) {
            list.remove();
        }
    });
}
// Дроплист сотрудников для поля "Команда"
function initMultiAutocomplete(inputId, options = {}) {
    const input = document.getElementById(inputId);
    if (!input) return;

    const {
        url = "/search_employees",
        minChars = 2,
        labelField = "label",
        valueField = "value",
        delimiter = ";"
    } = options;

    let timeout = null;

    input.addEventListener("input", () => {
        clearTimeout(timeout);

        let value = input.value;

        // Удаляем лишний разделитель, если он в конце и после него ничего нет
        if (value.endsWith(delimiter) && value.slice(-2) === delimiter + " ") {
            value = value.slice(0, -2) + delimiter;
        }

        // Автоматически добавляем ; если его нет после последнего табельника
        if (!value.endsWith(delimiter) && !value.endsWith(" ") && value.split(delimiter).length > 1) {
            const parts = value.split(delimiter);
            const last = parts[parts.length - 1].trim();

            // Если последний фрагмент — это валидный табельник (8 цифр)
            if (/^\d{8}$/.test(last)) {
                value += delimiter;
            }
        }

        // Убираем ; если после него ничего нет
        if (value.endsWith(delimiter)) {
            const parts = value.split(delimiter);
            const last = parts[parts.length - 1];
            if (last.trim() === "") {
                // ничего не делаем — пользователь начинает вводить
            }
        }

        input.value = value;

        const parts = value.split(delimiter);
        const currentQuery = parts[parts.length - 1].trim();

        if (currentQuery.length < minChars) return;

        timeout = setTimeout(() => {
            fetch(`${url}?q=${encodeURIComponent(currentQuery)}`)
                .then(res => res.json())
                .then(data => {
                    const existingList = input.parentNode.querySelector(".autocomplete-list");
                    if (existingList) existingList.remove();

                    const list = document.createElement("ul");
                    list.className = "autocomplete-list";
                    list.style.position = "absolute";
                    list.style.zIndex = "1000";
                    list.style.backgroundColor = "white";
                    list.style.border = "1px solid #ccc";
                    list.style.listStyle = "none";
                    list.style.padding = "0";
                    list.style.marginTop = "0";

                    data.forEach(item => {
                        const li = document.createElement("li");
                        li.textContent = item[labelField];
                        li.style.padding = "5px 10px";
                        li.style.cursor = "pointer";

                        li.addEventListener("click", () => {
                            // Заменяем последний фрагмент на выбранный табельник
                            parts[parts.length - 1] = item[valueField];
                            const cleanParts = [...new Set(parts.map(p => p.trim()).filter(p => p))];
                            input.value = cleanParts.join(delimiter) + delimiter; // сразу добавляем ; после выбора
                            list.remove();
                        });

                        list.appendChild(li);
                    });

                    input.parentNode.appendChild(list);
                });
        }, 300);
    });

    document.addEventListener("click", (e) => {
        const list = input.parentNode.querySelector(".autocomplete-list");
        if (list && !list.contains(e.target) && e.target !== input) {
            list.remove();
        }
    });
}

function searchTableValues(value) {

    const searchInput = document.getElementById(`search-input-${value}`);

    if (!searchInput) return;

    const clearIcon = document.getElementById(`clear-search-${value}`);
    const table = document.getElementById(`custom-table-${value}`);
    const rows = table.getElementsByTagName('tr');

    function filterTable() {
        const filter = searchInput.value.toLowerCase()

        clearIcon.style.display = filter ? 'block' : 'none';

        for (let i = 1; i < rows.length; i++) {
            const row = rows[i];
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(filter) ? '' : 'none';
        }
    }

    searchInput.addEventListener('input', filterTable);

    clearIcon.addEventListener('click', function () {
        searchInput.value = '';
        filterTable();
    });
}

function getTabCard() {
    const main_div = document.querySelectorAll('.clickable');
    
    if (!main_div) return

    main_div.forEach((header, index) => {
        header.addEventListener('click', () => {
            const allBlocks = document.querySelectorAll('.hidden-content');
            const thisBlock = allBlocks[index]

            const isAlreadyOpen = thisBlock.classList.contains('open')

            allBlocks.forEach(div => div.classList.remove('open'))

            if (!isAlreadyOpen) {
                thisBlock.classList.add('open')
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', function () {

    searchTableValues('user')
    searchTableValues('project')
    searchTableValues('index')
    getTabCard()

    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.classList.remove('show');
            alert.classList.add('hide');

            setTimeout(function () {
                alert.remove();
            }, 300);
        }, 5000);
    });

    getOtherFields('register-page-full-name');

    initAutocomplete("create-page-product-owner-autocomplete", {
        url: "/search_employees",
        valueField: "value",         // табельный номер
        labelField: "label",         // ФИО + отдел
        hiddenInputId: "create-page-product-owner-hidden"
    });

    initAutocomplete("create-page-curator-autocomplete", {
        url: "/search_employees",
        valueField: "value",         // табельный номер
        labelField: "label",         // ФИО + отдел
        hiddenInputId: "create-page-curator-hidden"
    });

    initMultiAutocomplete("create-page-team-autocomplete", {
        valueField: "value",         // табельный номер
        labelField: "label",         // ФИО, должность и т.п.
        delimiter: ";"               // Разделитель табельников
    });

    // TOOLTIPS 
    document.querySelectorAll(".input-with-tooltip").forEach(input => {
        input.addEventListener("focus", () => {
            const tooltip = document.getElementById("tooltip");
            const tooltipText = tooltip.querySelector(".tooltip-text");
            tooltipText.textContent = input.dataset.tooltip;

            const rect = input.getBoundingClientRect();
            tooltip.style.left = rect.left + window.scrollX + "px";
            tooltip.style.top = rect.top + window.scrollY - tooltip.offsetHeight + 60 + "px";
            tooltip.style.width = rect.width + "px";
            tooltip.style.display = "block";
        });

        input.addEventListener("input", () => {
            tooltip.style.display = "none"; // Скрываем при вводе текста
        });

        input.addEventListener("blur", () => {
            document.getElementById("tooltip").style.display = "none";
        });
    });

    // FLASH-ALERTS
    document.addEventListener("DOMContentLoaded", function () {
        const flashContainer = document.getElementById("flash-container");
        if (flashContainer) {
            setTimeout(() => {
            flashContainer.style.transition = "opacity 0.5s ease-out";
            flashContainer.style.opacity = "0";
            setTimeout(() => flashContainer.remove(), 500); // удалить после анимации
            }, 2000); // 2 секунды
        }
    });
});