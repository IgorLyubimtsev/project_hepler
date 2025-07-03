/**
 * Создаёт и возвращает элемент UL для списка автодополнения с базовыми стилями
 */
function createAutocompleteList() {
    const list = document.createElement("ul");
    list.className = "autocomplete-list";
    Object.assign(list.style, {
        position: "absolute",
        zIndex: "1000",
        backgroundColor: "white",
        border: "1px solid #ccc",
        listStyle: "none",
        padding: "0",
        marginTop: "0"
    });
    return list;
}

/**
 * Автозаполнение с подгрузкой данных и заполнением дополнительных полей по выбранному ФИО
 * Используется для поля ФИО с ID inputId
 */
function getOtherFields(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.addEventListener('input', () => {
        const query = input.value.trim();

        // Удаляем старый список, если он есть
        const existingList = input.parentNode.querySelector(".autocomplete-list");
        if (existingList) existingList.remove();

        if (query.length < 2) return;

        fetch(`/search_employee?q=${encodeURIComponent(query)}`)
            .then(res => {
                if (!res.ok) throw new Error("Ошибка сети при поиске сотрудника");
                return res.json();
            })
            .then(data => {
                if (!Array.isArray(data) || data.length === 0) return;

                const list = createAutocompleteList();

                data.forEach(item => {
                    const li = document.createElement("li");
                    li.textContent = item['full_name'];
                    li.style.padding = "5px 10px";
                    li.style.cursor = "pointer";

                    li.addEventListener("click", () => {
                        const staff_number = document.getElementById('register-page-staff-number');
                        const position = document.getElementById('register-page-position');
                        const department = document.getElementById('register-page-department');
                        const email = document.getElementById('register-page-email');

                        input.value = item['full_name'];
                        if (staff_number) staff_number.value = item['staff_number'] || "";
                        if (position) position.value = item['position'] || "";      // исправлено
                        if (department) department.value = item['department'] || ""; // исправлено
                        if (email) email.value = item['email'] || "";

                        list.remove();
                    });

                    list.appendChild(li);
                });

                input.parentNode.appendChild(list);
            })
            .catch(err => {
                console.error("Ошибка в getOtherFields:", err);
            });
    });

    // Закрытие списка при клике вне input и списка
    document.addEventListener("click", (e) => {
        const list = input.parentNode.querySelector(".autocomplete-list");
        if (list && !list.contains(e.target) && e.target !== input) {
            list.remove();
        }
    });
}

/**
 * Универсальный автокомплит с возможностью указать поля для метки и значения
 * И опциональным скрытым инпутом для табельного номера
 */
function initAutocomplete(inputId, options = {}) {
    const input = document.getElementById(inputId);
    if (!input) return;

    const {
        url = "/search_employees",
        minChars = 2,
        labelField = "label",
        valueField = "value",
        hiddenInputId = null,
        debounceDelay = 300
    } = options;

    let timeout = null;

    input.addEventListener("input", () => {
        clearTimeout(timeout);

        const query = input.value.trim();

        // Если меньше минимума - убираем список и выходим
        if (query.length < minChars) {
            const existingList = input.parentNode.querySelector(".autocomplete-list");
            if (existingList) existingList.remove();
            return;
        }

        timeout = setTimeout(() => {
            fetch(`${url}?q=${encodeURIComponent(query)}`)
                .then(res => {
                    if (!res.ok) throw new Error("Ошибка сети при поиске");
                    return res.json();
                })
                .then(data => {
                    const existingList = input.parentNode.querySelector(".autocomplete-list");
                    if (existingList) existingList.remove();

                    if (!Array.isArray(data) || data.length === 0) return;

                    const list = createAutocompleteList();

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
                })
                .catch(err => {
                    console.error("Ошибка в initAutocomplete:", err);
                });
        }, debounceDelay);
    });

    // Закрываем список при клике вне поля и списка
    document.addEventListener("click", (e) => {
        const list = input.parentNode.querySelector(".autocomplete-list");
        if (list && !list.contains(e.target) && e.target !== input) {
            list.remove();
        }
    });
}
/**
 * Множественный автокомплит для поля с разделителем (например, табельные номера через ;)
 */
function initMultiAutocomplete(inputId, options = {}) {
    const input = document.getElementById(inputId);
    if (!input) return;

    const {
        url = "/search_employees",
        minChars = 2,
        labelField = "label",
        valueField = "value",
        delimiter = ";",
        debounceDelay = 300
    } = options;

    let timeout = null;

    input.addEventListener("input", () => {
        clearTimeout(timeout);

        let value = input.value;

        // Удаляем лишние пробелы вокруг разделителей, добавляем разделитель, если нужно
        if (value.endsWith(delimiter + " ")) {
            value = value.slice(0, -2) + delimiter;
        }

        if (!value.endsWith(delimiter) && !value.endsWith(" ")) {
            const parts = value.split(delimiter);
            const last = parts[parts.length - 1].trim();

            if (/^\d{8}$/.test(last)) {
                value += delimiter;
            }
        }

        input.value = value;

        const parts = value.split(delimiter);
        const currentQuery = parts[parts.length - 1].trim();

        if (currentQuery.length < minChars) {
            const existingList = input.parentNode.querySelector(".autocomplete-list");
            if (existingList) existingList.remove();
            return;
        }

        timeout = setTimeout(() => {
            fetch(`${url}?q=${encodeURIComponent(currentQuery)}`)
                .then(res => {
                    if (!res.ok) throw new Error("Ошибка сети при поиске");
                    return res.json();
                })
                .then(data => {
                    const existingList = input.parentNode.querySelector(".autocomplete-list");
                    if (existingList) existingList.remove();

                    if (!Array.isArray(data) || data.length === 0) return;

                    const list = createAutocompleteList();

                    data.forEach(item => {
                        const li = document.createElement("li");
                        li.textContent = item[labelField];
                        li.style.padding = "5px 10px";
                        li.style.cursor = "pointer";

                        li.addEventListener("click", () => {
                            parts[parts.length - 1] = item[valueField];
                            // Убираем дубликаты и пустые значения
                            const cleanParts = [...new Set(parts.map(p => p.trim()).filter(p => p))];
                            input.value = cleanParts.join(delimiter) + delimiter;
                            list.remove();
                        });

                        list.appendChild(li);
                    });

                    input.parentNode.appendChild(list);
                })
                .catch(err => {
                    console.error("Ошибка в initMultiAutocomplete:", err);
                });
        }, debounceDelay);
    });

    // Закрытие списка при клике вне поля и списка
    document.addEventListener("click", (e) => {
        const list = input.parentNode.querySelector(".autocomplete-list");
        if (list && !list.contains(e.target) && e.target !== input) {
            list.remove();
        }
    });
}

/**
 * Фильтрация таблицы по введённому значению в поле поиска
 */
function searchTableValues(value) {
    const searchInput = document.getElementById(`search-input-${value}`);
    if (!searchInput) return;

    const clearIcon = document.getElementById(`clear-search-${value}`);
    const table = document.getElementById(`custom-table-${value}`);
    if (!table) return;
    const rows = table.getElementsByTagName('tr');

    function filterTable() {
        const filter = searchInput.value.toLowerCase();

        clearIcon.style.display = filter ? 'block' : 'none';

        const rowsCount = rows.length;
        for (let i = 1; i < rowsCount; i++) {
            const row = rows[i];
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(filter) ? '' : 'none';
        }
    }

    searchInput.addEventListener('input', filterTable);

    clearIcon.addEventListener('click', () => {
        searchInput.value = '';
        filterTable();
    });
}


/**
 * Открытие/закрытие табов по клику на заголовок
 */
function getTabCard() {
    const headers = document.querySelectorAll('.clickable');
    if (headers.length === 0) return;

    headers.forEach((header, index) => {
        header.addEventListener('click', () => {
            const allBlocks = document.querySelectorAll('.hidden-content');
            if (index >= allBlocks.length) return;

            const thisBlock = allBlocks[index];
            const isAlreadyOpen = thisBlock.classList.contains('open');

            allBlocks.forEach(div => div.classList.remove('open'));

            if (!isAlreadyOpen) {
                thisBlock.classList.add('open');
            }
        });
    });
}

/**
 * Инициализация всплывающих подсказок для input с классом .input-with-tooltip
 */
function initTooltips() {
    const tooltip = document.getElementById("tooltip");
    if (!tooltip) return;
    const tooltipText = tooltip.querySelector(".tooltip-text");

    document.querySelectorAll(".input-with-tooltip").forEach(input => {
        input.addEventListener("focus", () => {
            tooltipText.textContent = input.dataset.tooltip || "";

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
            tooltip.style.display = "none";
        });
    });
}

/**
 * Автоматическое скрытие flash-уведомлений с плавным исчезновением
 */
function initFlashAlerts() {
    const flashContainer = document.getElementById("flash-container");
    if (!flashContainer) return;

    setTimeout(() => {
        flashContainer.style.transition = "opacity 0.5s ease-out";
        flashContainer.style.opacity = "0";
        setTimeout(() => flashContainer.remove(), 500);
    }, 2000);
}

// === Основная точка входа ===
document.addEventListener('DOMContentLoaded', function () {
    // Инициализация поиска в таблицах
    searchTableValues('user');
    searchTableValues('project');
    searchTableValues('index');

    // Инициализация табов
    getTabCard();

    // Скрытие alert-уведомлений
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            alert.classList.add('hide');
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Инициализация автозаполнения
    getOtherFields('register-page-full-name');

    initAutocomplete("create-page-product-owner-autocomplete", {
        url: "/search_employees",
        valueField: "value",         // табельный номер
        labelField: "label",         // ФИО + отдел
        hiddenInputId: "create-page-product-owner-hidden"
    });

    initAutocomplete("create-page-curator-autocomplete", {
        url: "/search_employees",
        valueField: "value",
        labelField: "label",
        hiddenInputId: "create-page-curator-hidden"
    });

    initMultiAutocomplete("create-page-team-autocomplete", {
        valueField: "value",
        labelField: "label",
        delimiter: ";"
    });

    // Инициализация тултипов
    initTooltips();

    // Инициализация flash-уведомлений
    initFlashAlerts();
});