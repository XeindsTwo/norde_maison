document.addEventListener('DOMContentLoaded', function () {
    const tbody = document.querySelector('fieldset.module .wrapper table tbody');
    const totalFormsInput = document.querySelector('#id_variants-TOTAL_FORMS');

    function duplicateRow(row) {
        if (!row) return;

        let totalForms = parseInt(totalFormsInput.value, 10);

        // клонируем строку
        const clone = row.cloneNode(true);

        // обновляем id и name
        clone.id = clone.id.replace(/-\d+$/, `-${totalForms}`);
        clone.querySelectorAll('input, select, textarea').forEach(input => {
            if (input.name) {
                input.name = input.name.replace(/-\d+-/, `-${totalForms}-`);
                input.id = input.id.replace(/-\d+-/, `-${totalForms}-`);

                if (input.type === 'checkbox') input.checked = input.checked;
                else input.value = input.value;
            }
        });

        // вставляем клон под текущей строкой
        row.after(clone);

        // увеличиваем TOTAL_FORMS
        totalFormsInput.value = totalForms + 1;
    }

    // делегирование: один обработчик на tbody
    tbody.addEventListener('click', function (e) {
        if (e.target.classList.contains('duplicate-row-btn')) {
            const row = e.target.closest('tr.form-row');
            duplicateRow(row);
        }
    });
});