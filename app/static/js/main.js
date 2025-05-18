// JavaScript principal para funcionalidades compartidas

// Manejar alertas flash
document.addEventListener('DOMContentLoaded', function() {
    // Auto cerrar alertas después de 5 segundos
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Inicializar todos los tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar dropdowns
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });
});

// Función para crear gráficos de línea
function createLineChart(canvasId, labels, datasets, title = '') {
    var ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: title !== '',
                    text: title,
                    font: {
                        size: 16
                    }
                },
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Función para crear gráficos de barras
function createBarChart(canvasId, labels, datasets, title = '') {
    var ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: title !== '',
                    text: title,
                    font: {
                        size: 16
                    }
                },
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Función para crear gráficos circulares
function createPieChart(canvasId, labels, data, backgroundColor, title = '') {
    var ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColor,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: title !== '',
                    text: title,
                    font: {
                        size: 16
                    }
                },
                legend: {
                    position: 'right',
                }
            }
        }
    });
}

// Función para crear gráficos de comparación
function createComparisonChart(canvasId, labels, dataBefore, dataAfter, labelBefore, labelAfter, title = '') {
    var ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: labelBefore,
                    data: dataBefore,
                    backgroundColor: 'rgba(220, 53, 69, 0.7)',
                    borderColor: 'rgba(220, 53, 69, 1)',
                    borderWidth: 1
                },
                {
                    label: labelAfter,
                    data: dataAfter,
                    backgroundColor: 'rgba(25, 135, 84, 0.7)',
                    borderColor: 'rgba(25, 135, 84, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: title !== '',
                    text: title,
                    font: {
                        size: 16
                    }
                },
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Función para formatear moneda (PEN)
function formatCurrency(amount) {
    return 'S/ ' + parseFloat(amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

// Función para formatear números con separador de miles
function formatNumber(number) {
    return parseFloat(number).toLocaleString('es-PE');
}

// Función para obtener datos de productos mediante AJAX
function getProductoInfo(productoId, callback) {
    fetch(`/ventas/api/productos/${productoId}`)
        .then(response => response.json())
        .then(data => {
            callback(data);
        })
        .catch(error => {
            console.error('Error al obtener información del producto:', error);
        });
}

// Función para actualizar campos del formulario de ventas
function actualizarCamposProducto(productoId) {
    if (productoId) {
        getProductoInfo(productoId, function(data) {
            document.getElementById('precio_unitario').value = data.precio_unitario;
            
            // Actualizar stock disponible si existe el elemento
            const stockInfoElement = document.getElementById('stock-info');
            if (stockInfoElement) {
                stockInfoElement.textContent = `Stock disponible: ${data.stock_actual}`;
                
                // Actualizar la clase según el nivel de stock
                stockInfoElement.className = 'mt-2';
                if (data.stock_actual <= 0) {
                    stockInfoElement.classList.add('text-danger');
                } else if (data.stock_actual < 5) {
                    stockInfoElement.classList.add('text-warning');
                } else {
                    stockInfoElement.classList.add('text-success');
                }
            }
        });
    }
}

// Mostrar u ocultar spinner de carga
function toggleSpinner(show) {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.style.display = show ? 'block' : 'none';
    }
}