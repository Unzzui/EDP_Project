/**
 * KANBAN BOARD - EDP Project
 * Script para gestionar el tablero Kanban de seguimiento de EDPs
 */

// Esperar a que el DOM esté completamente cargado
document.addEventListener("DOMContentLoaded", function () {

	// Inicializar todas las funcionalidades

	initSocketIO();
	setupColumnVisibility();
	animateColumns();
	initKanbanBoard();
	actualizarContadoresTablero();
	setupKPIPanel();
	calcularTotalesColumna();
	setupColumnToggle();
	setupBuscador();
	observarCambiosTablero();
	setupSocketConnection();
	actualizarContenidoTarjeta();
	setupEnhancedToast();
	setupProgressIndicator();
	initLazyLoading();
	setupValidadosToggle();
	// setupBatchLoading();
	// Función para inicializar el lazy loading
	function initLazyLoading() {
		// Asegurarse de que las clases necesarias estén definidas en CSS
		const style = document.createElement("style");
		style.textContent = `
    .lazy-hidden {
      opacity: 0;
      transform: translateY(20px);
      transition: opacity 0.5s ease, transform 0.5s ease;
    }
    
    .lazy-visible {
      opacity: 1;
      transform: translateY(0);
    }
  `;
		document.head.appendChild(style);

		// Crear el observer con configuración optimizada
		const lazyObserver = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting) {
						const card = entry.target;

						// Aplicar animación más suave
						setTimeout(() => {
							card.classList.remove("lazy-hidden");
							card.classList.add("lazy-visible");
						}, 50 * (parseInt(card.dataset.lazyIndex) || 0)); // Escalonamiento sutil

						// Dejar de observar
						lazyObserver.unobserve(card);
					}
				});
			},
			{
				root: null,
				rootMargin: "200px", // Cargar con más anticipación
				threshold: 0.1,
			}
		);

		// Aplicar lazy loading a todas las columnas secuencialmente
		document
			.querySelectorAll(".kanban-column")
			.forEach((column, columnIndex) => {
				// Obtener todas las tarjetas de esta columna
				const cards = column.querySelectorAll(".kanban-item");

				// Aplicar lazy loading a tarjetas después de un cierto número en cada columna
				const visibleThreshold = 3; // Primeras 3 tarjetas visibles por columna

				cards.forEach((card, cardIndex) => {
					if (cardIndex >= visibleThreshold) {
						// Guardar índice para animación escalonada
						card.dataset.lazyIndex = cardIndex - visibleThreshold;

						// Aplicar clase para ocultar inicialmente
						card.classList.add("lazy-hidden");

						// Registrar para observación
						lazyObserver.observe(card);
					}
				});
			});
	}

	// Llamar a la función cuando el DOM esté listo
	document.addEventListener("DOMContentLoaded", function () {
		// Dar tiempo para que se renderice la UI inicial
		setTimeout(initLazyLoading, 300);
	});

	function setupValidadosToggle() {
		const toggleBtn = document.getElementById("toggle-validados-antiguos");

		if (toggleBtn) {
			// Agregar tooltip más descriptivo
			toggleBtn.setAttribute(
				"title",
				"Los EDPs validados hace más de 10 días son ocultados automáticamente para mejorar el rendimiento"
			);

			// Mejorar visualmente el contador
			const totalOcultos = parseInt(
				document.getElementById("total-validados-ocultos")?.textContent || "0"
			);

			if (totalOcultos > 0) {
				// Crear indicador más visible
				const indicador = document.createElement("div");
				indicador.className =
					"fixed bottom-16 left-4 bg-[color:var(--bg-card)] shadow-lg rounded-lg p-3 border border-[color:var(--border-color)] z-40";
				indicador.innerHTML = `
        <div class="flex items-center gap-3">
          <div class="flex flex-col">
            <span class="text-xs text-[color:var(--text-secondary)]">EDPs antiguos ocultos</span>
            <span class="font-bold text-lg">${totalOcultos}</span>
          </div>
          <button id="quick-show-validados" class="btn-outline text-xs py-1">
            Mostrar
          </button>
        </div>
      `;

				document.body.appendChild(indicador);

				// Configurar botón rápido
				document
					.getElementById("quick-show-validados")
					.addEventListener("click", () => {
						const url = new URL(window.location.href);
						url.searchParams.set("mostrar_validados_antiguos", "true");
						window.location.href = url.toString();
					});
			}
		}
	}

	// Sistema de notificaciones mejorado
	function setupEnhancedToast() {
		// Verificar si ya existe
		if (window.showToast) return;

		// Crear el contenedor de notificaciones si no existe
		let toastContainer = document.getElementById("toast-container");
		if (!toastContainer) {
			toastContainer = document.createElement("div");
			toastContainer.id = "toast-container";
			toastContainer.className =
				"fixed bottom-4 right-4 flex flex-col gap-3 z-50";
			document.body.appendChild(toastContainer);
		}

		// Implementar función mejorada
		window.showToast = function (message, type = "success", duration = 3000) {
			const toast = document.createElement("div");
			toast.className = `flex items-center p-4 mb-1 animate__animated animate__fadeInUp shadow-lg rounded-lg max-w-xs`;

			// Configurar estilo según tipo
			switch (type) {
				case "success":
					toast.classList.add(
						"bg-green-100",
						"border-l-4",
						"border-green-500",
						"text-green-700"
					);
					break;
				case "error":
					toast.classList.add(
						"bg-red-100",
						"border-l-4",
						"border-red-500",
						"text-red-700"
					);
					break;
				case "info":
					toast.classList.add(
						"bg-blue-100",
						"border-l-4",
						"border-blue-500",
						"text-blue-700"
					);
					break;
				case "warning":
					toast.classList.add(
						"bg-yellow-100",
						"border-l-4",
						"border-yellow-500",
						"text-yellow-700"
					);
					break;
			}

			// Contenido
			toast.innerHTML = `
      <div class="flex-shrink-0 mr-3">
        ${
					type === "success"
						? '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>'
						: ""
				}
        ${
					type === "error"
						? '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>'
						: ""
				}
        ${
					type === "info"
						? '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zm-1 9a1 1 0 100-2 1 1 0 000 2zm0 0V8a1 1 0 011-1h1a1 1 0 110 2h-1v4a1 1 0 01-1 1z" clip-rule="evenodd"></path></svg>'
						: ""
				}
        ${
					type === "warning"
						? '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>'
						: ""
				}
      </div>
      <div>${message}</div>
      <button class="ml-auto text-gray-400 hover:text-gray-900" onclick="this.parentElement.remove()">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
      </button>
    `;

			// Agregar al contenedor
			toastContainer.appendChild(toast);

			// Remover después del tiempo especificado
			setTimeout(() => {
				toast.classList.replace("animate__fadeInUp", "animate__fadeOutDown");
				setTimeout(() => toast.remove(), 500);
			}, duration);
		};
	}

	function setupProgressIndicator() {
		// Crear elemento para la barra de progreso
		const progressContainer = document.createElement("div");
		progressContainer.className = "fixed top-0 left-0 w-full z-50";
		progressContainer.innerHTML = `<div id="loading-progress-bar" class="h-1 bg-[color:var(--accent-blue)] transform scale-x-0 origin-left transition-transform duration-300"></div>`;
		document.body.appendChild(progressContainer);

		// Funciones para controlar el progreso
		window.showProgress = function () {
			const bar = document.getElementById("loading-progress-bar");
			bar.style.transform = "scaleX(0.3)";
			setTimeout(() => {
				bar.style.transform = "scaleX(0.65)";
			}, 500);
			setTimeout(() => {
				bar.style.transform = "scaleX(0.8)";
			}, 1200);
		};

		window.completeProgress = function () {
			const bar = document.getElementById("loading-progress-bar");
			bar.style.transform = "scaleX(1)";
			setTimeout(() => {
				bar.style.transform = "scaleX(0)";
			}, 700);
		};
	}
	const lazyLoadObserver = new IntersectionObserver(
		(entries, observer) => {
			entries.forEach((entry) => {
				if (entry.isIntersecting) {
					const item = entry.target;
					// Quitar la clase de oculto y animar la entrada
					item.classList.remove("opacity-0", "translate-y-4");
					item.classList.add("animate__fadeIn");
					observer.unobserve(item);
				}
			});
		},
		{
			root: null,
			rootMargin: "100px",
			threshold: 0.1,
		}
	);

	// Aplicar lazy loading a todos los kanban items
	document.querySelectorAll(".kanban-item").forEach((item, index) => {
		// Solo aplicar lazy loading después de los primeros 12 items (los más visibles)
		if (index > 11) {
			item.classList.add(
				"opacity-0",
				"translate-y-4",
				"transition-all",
				"duration-300"
			);
			lazyLoadObserver.observe(item);
		}
	});

	// Botón para mostrar/ocultar validados antiguos
	const toggleBtn = document.getElementById("toggle-validados-antiguos");
	if (toggleBtn) {
		toggleBtn.addEventListener("click", function () {
			// Obtener URL actual y parámetros
			const url = new URL(window.location.href);
			const mostrarActual =
				url.searchParams.get("mostrar_validados_antiguos") === "true";

			// Invertir valor
			url.searchParams.set("mostrar_validados_antiguos", !mostrarActual);

			// Redirigir manteniendo todos los filtros
			window.location.href = url.toString();
		});
	}
	// Sistema de notificaciones globales
	window.showToast = function (message, type = "success") {
		const toast = document.getElementById("toast-notification");
		const toastText = document.getElementById("toast-text");
		const toastIcon = document.getElementById("toast-icon");

		// Configurar contenido
		toastText.textContent = message;

		// Configurar icono y colores según tipo
		if (type === "success") {
			toastIcon.className =
				"inline-flex items-center justify-center flex-shrink-0 w-8 h-8 text-[color:var(--accent-green)] bg-[color:var(--state-success-bg)] rounded-lg";
			toastIcon.innerHTML =
				'<svg class="w-5 h-5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20"><path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Zm3.707 8.207-4 4a1 1 0 0 1-1.414 0l-2-2a1 1 0 0 1 1.414-1.414L9 10.586l3.293-3.293a1 1 0 0 1 1.414 1.414Z"/></svg>';
		} else if (type === "error") {
			toastIcon.className =
				"inline-flex items-center justify-center flex-shrink-0 w-8 h-8 text-[color:var(--accent-red)] bg-[color:var(--state-error-bg)] rounded-lg";
			toastIcon.innerHTML =
				'<svg class="w-5 h-5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20"><path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Zm3.5 11.793-2.293 2.293a1 1 0 0 1-1.414 0L7.5 12.293a1 1 0 1 1 1.414-1.414L10 11.965l1.086-1.086a1 1 0 0 1 1.414 1.414Z"/></svg>';
		} else if (type === "info") {
			toastIcon.className =
				"inline-flex items-center justify-center flex-shrink-0 w-8 h-8 text-[color:var(--accent-blue)] bg-[color:var(--state-info-bg)] rounded-lg";
			toastIcon.innerHTML =
				'<svg class="w-5 h-5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20"><path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Zm1 13.5a1 1 0 0 1-2 0V7.5a1 1 0 0 1 2 0v6.5Zm-1-8.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z"/></svg>';
		}

		// Mostrar notificación
		toast.classList.remove("hidden");
		toast.classList.add("animate__fadeInUp");

		// Ocultar después de 3 segundos
		setTimeout(() => {
			hideToast();
		}, 3000);
	};

	window.hideToast = function () {
		const toast = document.getElementById("toast-notification");
		toast.classList.remove("animate__fadeInUp");
		toast.classList.add("animate__fadeOutDown");
		setTimeout(() => {
			toast.classList.add("hidden");
			toast.classList.remove("animate__fadeOutDown");
		}, 500);
	};
});

// -------------------------------------------------------------
// Iniciaclizacion del SOCKET.IO
// -------------------------------------------------------------
function initSocketIO() {
	// Crear conexión
	const socket = io();

	// Gestionar estados de conexión
	socket.on("connect", () => {
		showToast("Conexión en tiempo real establecida", "info");
	});

	socket.on("disconnect", () => {
		showToast("Se perdió la conexión en tiempo real", "error");
	});

	// Escuchar actualizaciones
	socket.on("estado_actualizado", (data) => {
		// Destacar visualmente el cambio si se puede identificar la tarjeta
		if (data.edp_id) {
			const tarjeta = document.querySelector(
				`.kanban-item[data-id="${data.edp_id}"]`
			);
			if (tarjeta) {
				tarjeta.classList.add("highlight-update");
				setTimeout(() => tarjeta.classList.remove("highlight-update"), 2000);
			}
		}

		// Actualizar todos los contadores
		actualizarContadoresTablero();

		// Mostrar notificación
		showToast(`EDP actualizado: ${data.edp_id || "desconocido"}`, "info");
	});
}

/**
 * UTILIDADES Y AYUDANTES
 * Funciones básicas utilizadas por otras funciones
 */
function slugify(estado) {
	return estado
		.toLowerCase()
		.normalize("NFD") // separa tildes
		.replace(/[\u0300-\u036f]/g, "") // elimina diacríticos
		.replace(/\s+/g, "-"); // espacios → guión
}
/**
 * Formatea una fecha para campos input[type="date"]
 * @param {string} fechaStr - Fecha en cualquier formato
 * @returns {string} - Fecha en formato YYYY-MM-DD o cadena vacía
 */
function formatFecha(fechaStr) {
	if (!fechaStr) return "";

	// Si ya tiene formato YYYY-MM-DD
	if (/^\d{4}-\d{2}-\d{2}$/.test(fechaStr)) {
		return fechaStr;
	}

	try {
		// Intentar convertir usando Date
		const fecha = new Date(fechaStr);
		if (!isNaN(fecha.getTime())) {
			return fecha.toISOString().split("T")[0];
		}

		// Alternativa: parsear formatos comunes (DD/MM/YYYY)
		const partes = fechaStr.split(/[\/.-]/);
		if (partes.length === 3) {
			// Asumir formato DD/MM/YYYY
			if (
				partes[0].length <= 2 &&
				partes[1].length <= 2 &&
				partes[2].length === 4
			) {
				return `${partes[2]}-${partes[1].padStart(2, "0")}-${partes[0].padStart(
					2,
					"0"
				)}`;
			}
			// Formato YYYY/MM/DD
			else if (
				partes[0].length === 4 &&
				partes[1].length <= 2 &&
				partes[2].length <= 2
			) {
				return `${partes[0]}-${partes[1].padStart(2, "0")}-${partes[2].padStart(
					2,
					"0"
				)}`;
			}
		}
	} catch (error) {
		console.error("Error al formatear fecha:", fechaStr, error);
	}

	return "";
}

/**
 * Actualiza el contenido de una tarjeta manteniendo su estructura HTML original
 * @param {HTMLElement} item - Elemento DOM de la tarjeta
 * @param {Object} nuevosDatos - Nuevos datos para la tarjeta
 * @param {string} estadoDestino - Estado al que se movió la tarjeta
 */
function actualizarContenidoTarjeta(item, nuevosDatos, estadoDestino) {
	if (!nuevosDatos || Object.keys(nuevosDatos).length === 0) {
		console.warn("No hay datos para actualizar la tarjeta");
		return;
	}

	// 1. Actualizar la etiqueta de estado (pill)
	const estadoPill = item.querySelector(".estado-pill");
	if (estadoPill) {
		// Actualizar clase y texto
		estadoPill.className = `estado-pill estado-${estadoDestino.toLowerCase()}`;
		estadoPill.textContent = estadoDestino;
	}

	// 2. ESTRUCTURA EXISTENTE: Encontrar la sección info detallada
	const seccionDetalle = item.querySelector(".space-y-1.mb-2.text-xs");
	if (seccionDetalle) {
		// ELIMINAR elementos que podrían duplicarse al actualizar
		// (mantiene la estructura pero elimina los que se recrearán)
		const elementosAEliminar =
			seccionDetalle.querySelectorAll(".flex.items-center");
		elementosAEliminar.forEach((el) => el.remove());

		// 3. RECREAR elementos de fecha estimada de pago (siguiendo estructura exacta)
		if (nuevosDatos["Fecha Estimada de Pago"]) {
			const fechaPago = new Date(nuevosDatos["Fecha Estimada de Pago"]);
			const hoy = new Date();
			const diasParaPago = Math.round(
				(fechaPago - hoy) / (1000 * 60 * 60 * 24)
			);

			const fechaFormateada = formatFechaVisual(
				nuevosDatos["Fecha Estimada de Pago"]
			);

			// Crear div con estructura idéntica al template original
			const divPagoEstimado = document.createElement("div");
			divPagoEstimado.className = "flex items-center justify-between";

			// Decisión de mostrar pendiente o atrasado según conformidad
			let estadoTexto = "";
			if (nuevosDatos["Conformidad Enviada"] === "Sí") {
				estadoTexto =
					diasParaPago > 0
						? `(en ${diasParaPago} días)`
						: `(atrasado ${-diasParaPago} días)`;
			} else {
				estadoTexto = "(pendiente conf.)";
			}

			divPagoEstimado.innerHTML = `
        <span class="text-[color:var(--text-secondary)]">Pago estimado:</span>
        <span class="${
					diasParaPago > 0 ? "text-green-600" : "text-red-600 font-medium"
				}">
          ${fechaFormateada}
          <span class="ml-1 text-[0.65rem] ${
						nuevosDatos["Conformidad Enviada"] !== "Sí"
							? "text-[color:var(--accent-amber)]"
							: ""
					}">${estadoTexto}</span>
        </span>
      `;

			seccionDetalle.appendChild(divPagoEstimado);
		}

		// 4. RECREAR elemento de conformidad enviada
		if (nuevosDatos["Conformidad Enviada"] === "Sí") {
			const divConformidad = document.createElement("div");
			divConformidad.className = "flex items-center";

			// Formato idéntico al template
			const fechaConformidadStr = nuevosDatos["Fecha Conformidad"]
				? `<span class="ml-1 text-[color:var(--text-secondary)]">(${formatFechaVisual(
						nuevosDatos["Fecha Conformidad"]
				  )})</span>`
				: "";

			divConformidad.innerHTML = `
        <svg class="h-3 w-3 text-green-500 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        <span class="text-green-600">Conformidad enviada</span>
        ${fechaConformidadStr}
      `;

			seccionDetalle.appendChild(divConformidad);
		}
		// Si tiene fecha de envío pero no conformidad
		else if (nuevosDatos["Fecha Envío al Cliente"]) {
			const divEsperaConformidad = document.createElement("div");
			divEsperaConformidad.className = "flex items-center";
			divEsperaConformidad.innerHTML = `
        <svg class="h-3 w-3 text-[color:var(--accent-amber)] mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="text-[color:var(--accent-amber)]">Esperando conformidad</span>
      `;

			seccionDetalle.appendChild(divEsperaConformidad);
		}

		// 5. RECREAR N° de conformidad si existe
		if (nuevosDatos["N° Conformidad"]) {
			const divNumConformidad = document.createElement("div");
			divNumConformidad.className = "flex items-center";
			divNumConformidad.innerHTML = `
        <span class="text-[color:var(--text-secondary)]">N° Conf:</span>
        <span class="ml-1 px-1.5 bg-[color:var(--bg-highlight)] rounded">${nuevosDatos["N° Conformidad"]}</span>
      `;

			seccionDetalle.appendChild(divNumConformidad);
		}
	}

	// 6. Actualizar contador de días si existe
	const diasElement = item.querySelector(
		'p:has(svg[stroke-linecap="round"][stroke-linejoin="round"][d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"]) span'
	);
	if (diasElement && nuevosDatos["Días Espera"]) {
		const diasEspera = parseInt(nuevosDatos["Días Espera"]);
		const tieneConformidad =
			nuevosDatos["Conformidad Enviada"] === "Sí" &&
			nuevosDatos["Fecha Conformidad"];

		// Actualizar clases según cantidad de días
		diasElement.className = "";
		if (diasEspera > 5)
			diasElement.classList.add(
				"text-[color:var(--accent-amber)]",
				"font-bold"
			);
		if (diasEspera > 10)
			diasElement.classList.add("text-[color:var(--accent-red)]", "font-bold");

		// Actualizar texto
		diasElement.innerHTML = `
      ${diasEspera} días${tieneConformidad ? " (conf.)" : ""}
      ${diasEspera > 10 ? "⚠️" : ""}
    `;
	}

	// 7. Efecto de actualización para feedback visual
	item.classList.add("contenido-actualizado");
	setTimeout(() => {
		item.classList.remove("contenido-actualizado");
	}, 2000);
}

/**
 * Formatea fechas para mostrarlas en formato DD-MM-YYYY
 */
function formatFechaVisual(fechaStr) {
	if (!fechaStr) return "";

	try {
		// Si ya es un objeto Date, formatear directamente
		if (fechaStr instanceof Date) {
			return `${String(fechaStr.getDate()).padStart(2, "0")}-${String(
				fechaStr.getMonth() + 1
			).padStart(2, "0")}-${fechaStr.getFullYear()}`;
		}

		// Si es formato ISO YYYY-MM-DD
		if (typeof fechaStr === "string" && fechaStr.includes("-")) {
			const partes = fechaStr.split("T")[0].split("-");
			if (partes.length === 3) {
				return `${partes[2]}-${partes[1]}-${partes[0]}`;
			}
		}

		// Intentar convertir al formato requerido
		const fecha = new Date(fechaStr);
		if (!isNaN(fecha.getTime())) {
			return `${String(fecha.getDate()).padStart(2, "0")}-${String(
				fecha.getMonth() + 1
			).padStart(2, "0")}-${fecha.getFullYear()}`;
		}

		return fechaStr; // Si no se puede formatear, devolver el valor original
	} catch (error) {
		console.error("Error al formatear fecha:", error);
		return fechaStr;
	}
}

/**
 * Formatea una fecha ISO en formato visual DD-MM-YYYY
 */
function formatFechaVisual(fechaStr) {
	if (!fechaStr) return "";

	try {
		// Si es formato ISO o YYYY-MM-DD
		if (fechaStr.includes("-")) {
			const partes = fechaStr.split("T")[0].split("-");
			return `${partes[2]}-${partes[1]}-${partes[0]}`;
		}

		// Si ya tiene el formato DD-MM-YYYY
		if (fechaStr.includes("/")) {
			return fechaStr.replace(/\//g, "-");
		}

		return fechaStr;
	} catch (error) {
		console.error("Error al formatear fecha visual:", fechaStr, error);
		return fechaStr;
	}
}
/**
 * Actualiza el contador de columnas ocultas
 */
function actualizarIndicadorColumnasOcultas() {
	const toggles = document.querySelectorAll(".toggle-column:not(:checked)");
	const columnasOcultas = toggles.length;

	// Buscar o crear el indicador de columnas ocultas
	let indicador = document.getElementById("columnas-ocultas-indicador");
	if (!indicador) {
		indicador = document.createElement("div");
		indicador.id = "columnas-ocultas-indicador";
		indicador.className =
			"fixed bottom-4 left-4 bg-[color:var(--bg-card)] text-[color:var(--text-primary)] px-4 py-2 rounded-lg shadow-lg border border-[color:var(--border-color)] z-50 animate__animated";
		document.body.appendChild(indicador);
	}

	// Actualizar contenido
	if (columnasOcultas > 0) {
		indicador.innerHTML = `
      <div class="flex items-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 text-[color:var(--accent-amber)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>${columnasOcultas} columna${
			columnasOcultas !== 1 ? "s" : ""
		} oculta${columnasOcultas !== 1 ? "s" : ""}</span>
      </div>
    `;
		indicador.classList.remove("hidden", "animate__fadeOut");
		indicador.classList.add("animate__fadeIn");
	} else {
		indicador.classList.remove("animate__fadeIn");
		indicador.classList.add("animate__fadeOut");
		setTimeout(() => {
			indicador.classList.add("hidden");
		}, 300);
	}
}

function refrescarCabecerasColumnas() {
	document.querySelectorAll(".kanban-column").forEach((col) => {
		const total = col.querySelectorAll(".kanban-item").length;
		const pill = col.querySelector(".estado-pill"); // el span de la cabecera
		if (pill) pill.textContent = total;
	});
}

/**
 * ANIMACIONES Y EFECTOS VISUALES
 * Funciones para animar elementos de la interfaz
 */

/**
 * Anima la entrada de columnas y tarjetas al cargar la página
 */
function animateColumns() {
	const columns = document.querySelectorAll(".kanban-column");

	columns.forEach((col, index) => {
		// Asignar índice para animación escalonada
		col.style.setProperty("--column-index", index);

		// Añadir clases de animación
		col.classList.add(
			"animate__animated",
			"animate__fadeInRight",
			"animate-columna"
		);

		// Animar las tarjetas dentro de cada columna con retraso
		const cards = col.querySelectorAll(".kanban-item");
		cards.forEach((card, cardIndex) => {
			card.style.opacity = "0";
			setTimeout(() => {
				card.style.opacity = "1";
				card.classList.add("animate__animated", "animate__fadeInUp");
				setTimeout(() => {
					card.classList.remove("animate__animated", "animate__fadeInUp");
				}, 500);
			}, 300 + index * 100 + cardIndex * 50);
		});
	});
}

/**
 * Ordena las tarjetas de una lista por días transcurridos (mayor a menor)
 */
function ordenarTarjetasPorDias(lista) {
	// Obtener todas las tarjetas
	const tarjetas = Array.from(lista.querySelectorAll(".kanban-item"));

	// Si no hay tarjetas o solo hay una, no es necesario ordenar
	if (tarjetas.length <= 1) return;

	// Ordenar tarjetas por días (mayor a menor)
	tarjetas.sort((a, b) => {
		// Encontrar el elemento que contiene los días
		const diasTextoA =
			a.querySelector('svg[stroke="currentColor"] + span')?.textContent || "";
		const diasTextoB =
			b.querySelector('svg[stroke="currentColor"] + span')?.textContent || "";

		// Extraer número de días
		const diasA = parseInt(diasTextoA) || 0;
		const diasB = parseInt(diasTextoB) || 0;

		// Ordenar de mayor a menor
		return diasB - diasA;
	});

	// Aplicar animación suave a las tarjetas que cambiarán de posición
	tarjetas.forEach((tarjeta) => {
		tarjeta.style.transition = "transform 0.5s ease";
	});

	// Reordenar en el DOM con animación
	tarjetas.forEach((tarjeta) => {
		// Añadimos un pequeño retraso para permitir que las transiciones funcionen
		setTimeout(() => {
			lista.appendChild(tarjeta);
		}, 50);
	});
}

/**
 * GESTIÓN DE DATOS Y ESTADOS
 * Funciones para actualizar datos y métricas
 */

/**
 * Calcula y muestra totales financieros y días promedio por columna
 */
function calcularTotalesColumna() {
	const columns = document.querySelectorAll(".kanban-column");

	columns.forEach((col) => {
		const estado = col.dataset.estado;
		const tarjetas = col.querySelectorAll(".kanban-item");

		// Calcular total financiero
		let totalMonto = 0;
		let totalDias = 0;
		let tarjetasConDias = 0;
		tarjetas.forEach((tarjeta) => {
			// Sumar montos
			const montoText = tarjeta
				.querySelector("span[data-tooltip]")
				.textContent.trim();
			const monto = parseFloat(
				montoText.replace("$", "").replace(/\./g, "").replace(",", ".")
			);
			if (!isNaN(monto)) {
				totalMonto += monto;
			}

			// Calcular días promedio según las reglas actualizadas
			const diasTextoCompleto = tarjeta.querySelector(
				'svg[stroke="currentColor"] + span'
			)?.textContent;
			if (diasTextoCompleto) {
				// Extraer solo el número de días (ignorando el texto adicional como "(conf.)")
				const diasMatch = diasTextoCompleto.match(/(\d+)/);
				if (diasMatch && diasMatch[1]) {
					const dias = parseInt(diasMatch[1]);
					if (!isNaN(dias)) {
						totalDias += dias;
						tarjetasConDias++;
					}
				}
			}
		});

		// Actualizar totales en la columna
		const totalElement = col.querySelector(`[data-columna-total="${estado}"]`);
		if (totalElement) {
			totalElement.textContent = `$${totalMonto.toLocaleString("es-CL")}`;
		}

		// Actualizar días promedio
		const diasElement = col.querySelector(`[data-columna-dias="${estado}"]`);
		if (diasElement) {
			const promedioDias =
				tarjetasConDias > 0 ? Math.round(totalDias / tarjetasConDias) : 0;
			diasElement.textContent = `${promedioDias} días prom.`;
		}
	});
}

/**
 * Actualiza el panel de resumen con estadísticas generales
 */
function updateSummaryPanel() {
	const summaryPanel = document
		.getElementById("summary-panel")
		.querySelector(".grid");
	const columns = document.querySelectorAll(".kanban-column");

	let totalTarjetas = 0;
	let tarjetasCriticas = 0;
	let diasPromedio = 0;
	let totalDias = 0;
	let tarjetasConDias = 0;

	// Recopilar datos
	columns.forEach((col) => {
		const estado = col.dataset.estado;
		const tarjetas = col.querySelectorAll(".kanban-item");

		// Contar tarjetas por estado
		totalTarjetas += tarjetas.length;
		// Contar días espera y críticos
		tarjetas.forEach((tarjeta) => {
			const diasElem = tarjeta.querySelector(
				'span[class*="text-[color:var(--accent-amber)]"], span[class*="text-[color:var(--accent-red)]"]'
			);
			if (diasElem) {
				const diasTexto = diasElem.textContent.trim();
				const dias = parseInt(diasTexto);
				if (!isNaN(dias)) {
					totalDias += dias;
					tarjetasConDias++;

					if (dias > 10) {
						tarjetasCriticas++;
					}
				}
			}
		});
	});

	// Calcular promedio
	diasPromedio =
		tarjetasConDias > 0 ? Math.round(totalDias / tarjetasConDias) : 0;

	// Construir HTML para el resumen
	let summaryHTML = `
    <div class="metric-card p-5">
      <p class="metric-label">Total EDPs</p>
      <p class="metric-value">${totalTarjetas}</p>
    </div>
    
    <div class="metric-card p-5">
      <p class="metric-label">Días promedio</p>
      <p class="metric-value">${diasPromedio}</p>
    </div>
    
    <div class="metric-card p-5">
      <p class="metric-label">Críticos</p>
      <p class="metric-value text-[color:var(--accent-red)]">${tarjetasCriticas}</p>
    </div>
    
    <div class="metric-card p-5">
      <p class="metric-label">Distribución</p>
      <div class="flex justify-around w-full mt-2">
  `;

	// Añadir contadores por estado
	columns.forEach((col) => {
		const estado = col.dataset.estado;
		const count = col.querySelectorAll(".kanban-item").length;
		const estadoClass = `estado-${estado.toLowerCase()}`;

		summaryHTML += `
      <div class="text-center">
        <span class="estado-pill ${estadoClass} mx-auto mb-1">${count}</span>
        <span class="text-xs block">${estado}</span>
      </div>
    `;
	});

	summaryHTML += `
      </div>
    </div>
  `;

	// Insertar en el DOM
	summaryPanel.innerHTML = summaryHTML;
}

/**
 * Mejora el Panel de KPIs con métricas estratégicas
 */
function setupKPIPanel() {
    // Recopilamos datos
    const columns = document.querySelectorAll(".kanban-column");
    let totalEDPs = 0;
    let totalMontoGeneral = 0;
    let totalMontoPagado = 0;
    let totalPendiente = 0;
    let edpsCriticos = 0;
    let diasTotales = 0;
    let tarjetasConDias = 0;

    columns.forEach((col) => {
        const estado = col.dataset.estado;
        const tarjetas = col.querySelectorAll(".kanban-item");

        totalEDPs += tarjetas.length;
        tarjetas.forEach((tarjeta) => {
            // Obtener el monto
            const montoElement = tarjeta.querySelector("span[data-tooltip]");
            if (!montoElement) return;
            
            const montoText = montoElement.textContent.trim();
            const monto = parseFloat(
                montoText.replace("$", "").replace(/\./g, "").replace(",", ".")
            );

            if (!isNaN(monto)) {
                totalMontoGeneral += monto;

                if (estado.toLowerCase() === "pagado" || estado.toLowerCase() === "validado") {
                    totalMontoPagado += monto;
                }
                if (estado.toLowerCase() === "revisión" || estado.toLowerCase() === "enviado") {
                    totalPendiente += monto;
                }
            }
            
            // Contabilizar días y tarjetas críticas
            const diasElement = tarjeta.querySelector('svg[stroke="currentColor"] + span');
            if (diasElement) {
                const diasMatch = diasElement.textContent.match(/(\d+)/);
                if (diasMatch && diasMatch[1]) {
                    const dias = parseInt(diasMatch[1]);
                    if (!isNaN(dias)) {
                        diasTotales += dias;
                        tarjetasConDias++;
                        
                        if (dias > 10) {
                            edpsCriticos++;
                        }
                    }
                }
            }
        });
    });
    
    // Calcular valores derivados
    const porcentajeAvance = totalMontoGeneral > 0 
        ? Math.round((totalMontoPagado / totalMontoGeneral) * 100) 
        : 0;
    
    const diasPromedio = tarjetasConDias > 0 
        ? Math.round(diasTotales / tarjetasConDias) 
        : 0;
    
    // Calcular tendencia (simulada - en producción obtendría datos históricos)
    const tendenciaMes = Math.random() > 0.5 ? '+5%' : '-3%'; 
    const esTendenciaPositiva = tendenciaMes.startsWith('+');
    
    // Actualizar métricas adicionales
    document.getElementById('edps-criticos').textContent = edpsCriticos;
    document.getElementById('dias-promedio').textContent = diasPromedio;
    document.getElementById('meta-mensual').textContent = formatCurrency_Kanban(1200000000); // Meta 20% superior
    
    const proyeccionElement = document.getElementById('proyeccion-tendencia');
    proyeccionElement.textContent = tendenciaMes;
    proyeccionElement.className = `text-lg font-bold ${esTendenciaPositiva ? 'text-[color:var(--accent-green)]' : 'text-[color:var(--accent-red)]'}`;
    
    // Actualizar icono de tendencia
    const iconoTendencia = proyeccionElement.nextElementSibling;
    if (esTendenciaPositiva) {
        iconoTendencia.classList.replace('text-[color:var(--accent-red)]', 'text-[color:var(--accent-green)]');
        iconoTendencia.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />';
    } else {
        iconoTendencia.classList.replace('text-[color:var(--accent-green)]', 'text-[color:var(--accent-red)]');
        iconoTendencia.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0v-8m0 8l-8-8-4 4-6-6" />';
    }

    // Actualizar HTML del panel de KPIs
    const summaryPanel = document.getElementById("summary-panel").querySelector(".grid");
    const lastUpdated = document.getElementById("last-updated-date");
    if (lastUpdated) {
        const now = new Date();
        lastUpdated.textContent = `Actualizado: ${now.toLocaleTimeString()}`;
    }
    
       summaryPanel.innerHTML = `
        <!-- Tarjeta 1: Total EDPs -->
        <div class="metric-card relative p-6 border-r border-b border-[color:var(--border-color-subtle)]">
            <div class="absolute top-0 left-0 w-full h-1 bg-[color:var(--accent-blue)] opacity-70"></div>
            <div class="flex flex-col">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-[color:var(--text-secondary)]">Total EDPs</span>
                    <div class="p-1.5 rounded-full bg-[color:var(--bg-subtle)]">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-[color:var(--accent-blue)]" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                            <path fill-rule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd" />
                        </svg>
                    </div>
                </div>
                <div class="flex items-end gap-2">
                    <span class="text-3xl font-bold">${totalEDPs}</span>
                    <span class="text-xs text-[color:var(--text-secondary)] mb-1">en seguimiento</span>
                </div>
                <div class="mt-auto pt-3 text-xs text-[color:var(--text-secondary)] flex items-center justify-between">
                    <span>Distribución:</span>
                    <div class="flex gap-1">
                        ${generarDistribucionHTML(columns)}
                    </div>
                </div>
            </div>
        </div>

        <!-- Tarjeta 2: Total por Cobrar -->
        <div class="metric-card relative p-6 border-r border-b border-[color:var(--border-color-subtle)]">
            <div class="absolute top-0 left-0 w-full h-1 bg-[color:var(--accent-blue)] opacity-70"></div>
            <div class="flex flex-col h-full">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-[color:var(--text-secondary)]">Total por Cobrar</span>
                    <div class="p-1.5 rounded-full bg-[color:var(--bg-subtle)]">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-[color:var(--accent-blue)]" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd" />
                        </svg>
                    </div>
                </div>
                <div>
                    <span class="text-2xl font-bold">${formatCurrency_Kanban(totalMontoGeneral)}</span>
                </div>
                <div class="mt-2 text-xs flex items-center text-[color:var(--text-secondary)]">
                    <span>Año fiscal en curso</span>
                </div>
                <div class="mt-auto pt-3 text-xs flex justify-between">
                    <span class="text-[color:var(--accent-amber)]">Vencimientos:</span>
                    <span class="font-medium">3 EDPs esta semana</span>
                </div>
            </div>
        </div>

        <!-- Tarjeta 3: Pendiente -->
        <div class="metric-card relative p-6 border-r border-b border-[color:var(--border-color-subtle)]">
            <div class="absolute top-0 left-0 w-full h-1 bg-[color:var(--accent-amber)] opacity-70"></div>
            <div class="flex flex-col h-full">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-[color:var(--text-secondary)]">Pendiente</span>
                    <div class="p-1.5 rounded-full bg-[color:var(--bg-subtle)]">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-[color:var(--accent-amber)]" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
                        </svg>
                    </div>
                </div>
                <div>
                    <span class="text-2xl font-bold">${formatCurrency_Kanban(totalPendiente)}</span>
                </div>
                <div class="mt-2 text-xs flex items-center text-[color:var(--text-secondary)]">
                    <span>En proceso de aprobación</span>
                </div>
                <div class="mt-auto pt-3">
                    <div class="flex justify-between items-center text-xs">
                        <span class="text-[color:var(--text-secondary)]">Progreso:</span>
                        <span class="font-medium">${Math.round((totalPendiente / totalMontoGeneral) * 100)}%</span>
                    </div>
                    <div class="w-full bg-[color:var(--bg-subtle)] h-1.5 mt-1.5 rounded-full overflow-hidden">
                        <div class="h-full bg-[color:var(--accent-amber)]" style="width: ${Math.round((totalPendiente / totalMontoGeneral) * 100)}%"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tarjeta 4: Pagado -->
        <div class="metric-card relative p-6 border-r border-b border-[color:var(--border-color-subtle)]">
            <div class="absolute top-0 left-0 w-full h-1 bg-[color:var(--accent-green)] opacity-70"></div>
            <div class="flex flex-col h-full">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-[color:var(--text-secondary)]">Pagado</span>
                    <div class="p-1.5 rounded-full bg-[color:var(--bg-subtle)]">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-[color:var(--accent-green)]" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                        </svg>
                    </div>
                </div>
                <div>
                    <span class="text-2xl font-bold text-[color:var(--accent-green)]">${formatCurrency_Kanban(totalMontoPagado)}</span>
                </div>
                <div class="mt-2 text-xs flex items-center text-[color:var(--text-secondary)]">
                    <span>Completados y procesados</span>
                </div>
                <div class="mt-auto pt-3">
                    <div class="flex justify-between items-center text-xs">
                        <span class="text-[color:var(--text-secondary)]">Último pagado:</span>
                        <span class="font-medium">25-05-2025</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tarjeta 5: Avance -->
        <div class="metric-card relative p-6 border-b border-[color:var(--border-color-subtle)]">
            <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-[color:var(--accent-blue)] to-[color:var(--accent-green)] opacity-70"></div>
            <div class="flex flex-col h-full">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-[color:var(--text-secondary)]">Avance Financiero</span>
                    <div class="p-1.5 rounded-full bg-[color:var(--bg-subtle)]">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-[color:var(--accent-blue)]" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
                            <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
                        </svg>
                    </div>
                </div>
                
                <div class="flex flex-col items-center justify-center mt-3">
                    <!-- Gráfico circular -->
                    <div class="relative w-24 h-24">
                        <svg class="w-full h-full" viewBox="0 0 36 36">
                            <!-- Fondo del gráfico -->
                            <path 
                                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                                fill="none" 
                                stroke="var(--bg-subtle)" 
                                stroke-width="3" 
                            />
                            <!-- Progreso del gráfico -->
                            <path 
                                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                                fill="none" 
                                stroke="var(--accent-green)" 
                                stroke-width="3" 
                                stroke-dasharray="${porcentajeAvance}, 100" 
                                stroke-linecap="round"
                            />
                            <!-- Texto central -->
                            <text x="18" y="20.35" class="percentage" text-anchor="middle" fill="var(--text-primary)" font-size="8.5" font-weight="bold">${porcentajeAvance}%</text>
                        </svg>
                    </div>
                    
                    <!-- Leyenda -->
                    <div class="w-full flex justify-between text-xs text-[color:var(--text-secondary)] mt-4">
                        <span>Cobrado</span>
                        <span>Por cobrar</span>
                    </div>
                    <div class="w-full bg-[color:var(--bg-subtle)] h-1.5 mt-1.5 rounded-full overflow-hidden">
                        <div class="h-full bg-[color:var(--accent-green)]" style="width: ${porcentajeAvance}%"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    
    // Configurar el botón de refresh
    document.getElementById('refresh-metrics')?.addEventListener('click', function() {
        this.classList.add('animate-spin');
        setTimeout(() => {
            actualizarContadoresTablero();
            this.classList.remove('animate-spin');
        }, 700);
    });
}

// Función auxiliar para generar la distribución visual
function generarDistribucionHTML(columns) {
    let html = '';
    const estados = {
        'revisión': 'bg-[color:var(--accent-blue)]',
        'enviado': 'bg-[color:var(--accent-amber)]',
        'pagado': 'bg-[color:var(--accent-amber-dark)]',
        'validado': 'bg-[color:var(--accent-green)]'
    };
    
    columns.forEach(col => {
        const estado = col.dataset.estado.toLowerCase();
        const count = col.querySelectorAll('.kanban-item').length;
        const bgColor = estados[estado] || 'bg-gray-400';
        
        html += `<span class="inline-flex items-center" title="${estado}: ${count}">
            <span class="w-2 h-2 rounded-full ${bgColor} mr-0.5"></span>${count}
        </span>`;
    });
    
    return html;
}

function formatCurrency_Kanban(amount) {
    return `$${amount.toLocaleString("es-CL")}`;
}
/**
 * Actualiza todos los contadores y métricas de manera centralizada
 */
function actualizarContadoresTablero() {
	// Aplicar animación para indicar actualización
	const metricas = document.querySelectorAll(".metric-value");
	metricas.forEach((metrica) => {
		metrica.classList.add("highlight");
		setTimeout(() => {
			metrica.classList.remove("highlight");
		}, 800);
	});

	refrescarCabecerasColumnas();

	// Actualizar todos los contadores y métricas
	updateSummaryPanel();
	calcularTotalesColumna();
	setupKPIPanel();

	// Verificar estado de columnas vacías
	document.querySelectorAll(".kanban-column").forEach((col) => {
		const estaVacia = col.querySelectorAll(".kanban-item").length === 0;
		col.setAttribute("data-empty", estaVacia);
	});
}

/**
 * Versión mejorada del observador de cambios
 */
function observarCambiosTablero() {
	// Crear un observador más potente que detecte cualquier cambio en el tablero
	const observer = new MutationObserver((mutations) => {
		// Flag para evitar múltiples actualizaciones en rápida sucesión
		let debeTriggerActualizacion = false;

		mutations.forEach((mutation) => {
			// Detectar cambios en contenido DOM que afecten a las tarjetas
			if (
				mutation.type === "childList" &&
				(mutation.addedNodes.length > 0 || mutation.removedNodes.length > 0)
			) {
				// Verificar si es un cambio relevante (afecta a tarjetas kanban)
				const esItemKanban = Array.from(mutation.addedNodes).some(
					(node) =>
						node.nodeType === 1 &&
						(node.classList?.contains("kanban-item") ||
							node.querySelector?.(".kanban-item"))
				);

				const eliminoItemKanban = Array.from(mutation.removedNodes).some(
					(node) =>
						node.nodeType === 1 &&
						(node.classList?.contains("kanban-item") ||
							node.querySelector?.(".kanban-item"))
				);

				if (esItemKanban || eliminoItemKanban) {
					debeTriggerActualizacion = true;
				}
			}

			// Detectar cambios de atributos (como data-empty)
			if (
				mutation.type === "attributes" &&
				(mutation.attributeName === "data-empty" ||
					(mutation.attributeName === "class" &&
						mutation.target.classList.contains("column-hidden")))
			) {
				debeTriggerActualizacion = true;
			}
		});

		// Si se detectaron cambios relevantes, actualizar después de un breve retraso
		if (debeTriggerActualizacion) {
			clearTimeout(window.contadoresTimeout);
			window.contadoresTimeout = setTimeout(() => {
				actualizarContadoresTablero();
			}, 250);
		}
	});

	// Configurar el observador para monitorear todo el tablero Kanban
	const kanbanBoard = document.getElementById("kanban-board");

	// Configuración más completa para el observer
	const config = {
		childList: true,
		attributes: true,
		subtree: true,
		attributeFilter: ["class", "data-empty", "style"],
	};

	observer.observe(kanbanBoard, config);

	// También observar el panel de resumen para detectar cambios allí
	const summaryPanel = document.getElementById("summary-panel");
	observer.observe(summaryPanel, config);
}

/**
 * FUNCIONES DE INTERACCIÓN DE USUARIO
 */

/**
 * Configura la visibilidad de columnas mediante checkboxes y ajusta el grid
 */
function setupColumnVisibility() {
	const toggles = document.querySelectorAll(".toggle-column");
	const kanbanBoard = document.getElementById("kanban-board");

	// Función para actualizar el diseño del grid
	const updateGridLayout = () => {
		const visibleColumns = document.querySelectorAll(
			".kanban-column:not(.column-hidden)"
		).length;

		// Eliminar todas las clases de grid existentes
		kanbanBoard.className = kanbanBoard.className.replace(/grid-cols-\d+/g, "");
		kanbanBoard.className = kanbanBoard.className.replace(
			/md:grid-cols-\d+/g,
			""
		);
		kanbanBoard.className = kanbanBoard.className.replace(
			/lg:grid-cols-\d+/g,
			""
		);

		// Aplicar nueva clase de grid según columnas visibles
		if (visibleColumns === 1) {
			kanbanBoard.classList.add("grid-cols-1");
		} else if (visibleColumns === 2) {
			kanbanBoard.classList.add("grid-cols-2");
		} else if (visibleColumns === 3) {
			kanbanBoard.classList.add("md:grid-cols-3");
		} else {
			kanbanBoard.classList.add("md:grid-cols-2", "lg:grid-cols-4");
		}
	};

	toggles.forEach((toggle) => {
		toggle.addEventListener("change", function () {
			const estado = this.dataset.estado;
			const columna = document.querySelector(
				`.kanban-column[data-estado="${estado}"]`
			);

			// Aplicar clase con animación
			if (this.checked) {
				columna.style.display = "";
				setTimeout(() => {
					columna.classList.remove("column-hidden");
					columna.classList.add("animate__animated", "animate__fadeIn");
					setTimeout(() => {
						columna.classList.remove("animate__animated", "animate__fadeIn");
					}, 500);
					updateGridLayout();
				}, 10);
			} else {
				columna.classList.add("animate__animated", "animate__fadeOut");
				setTimeout(() => {
					columna.classList.add("column-hidden");
					columna.classList.remove("animate__animated", "animate__fadeOut");
					updateGridLayout();
				}, 500);
			}

			// Actualizar el indicador de columnas ocultas
			actualizarIndicadorColumnasOcultas();

			// Actualizar totales después de cambiar visibilidad
			setTimeout(() => {
				calcularTotalesColumna();
				setupKPIPanel();
			}, 400);
		});
	});

	// Inicializar layout al cargar
	updateGridLayout();

	// También llamarlo al inicializarse
	actualizarIndicadorColumnasOcultas();
}

/**
 * Configura el botón toggle para ocultar/mostrar columnas vacías
 */
function setupColumnToggle() {
	const toggleBtn = document.getElementById("toggleEmptyColumns");
	let columnsHidden = false;

	toggleBtn.addEventListener("click", function () {
		const emptyColumns = document.querySelectorAll(
			'.kanban-column[data-empty="True"]'
		);

		if (columnsHidden) {
			// Mostrar columnas
			emptyColumns.forEach((col) => {
				col.classList.remove("column-hidden");
			});
			toggleBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 text-[color:var(--accent-blue)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
        Ocultar columnas vacías
      `;
			columnsHidden = false;
		} else {
			// Ocultar columnas
			emptyColumns.forEach((col) => {
				col.classList.add("column-hidden");
			});
			toggleBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 text-[color:var(--accent-blue)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
        Mostrar todas las columnas
      `;
			columnsHidden = true;
		}
	});
}

/**
 * Implementa la búsqueda avanzada de EDPs en el kanban con resaltado inteligente
 */
function setupBuscador() {
	const inputBuscar = document.getElementById("buscar-edp");
	const botonLimpiar = document.getElementById("limpiar-busqueda");
	const resultadosContainer = document.getElementById("resultados-busqueda");
	let timeoutId = null;

	// Función debounced para evitar búsquedas excesivas mientras se escribe
	const buscarDebounced = (query) => {
		clearTimeout(timeoutId);
		timeoutId = setTimeout(() => realizarBusqueda(query), 300);
	};

	// Función principal de búsqueda
	const realizarBusqueda = (query) => {
		query = query.toLowerCase().trim();
		const items = document.querySelectorAll(".kanban-item");
		let coincidencias = 0;

		// Remover destacados previos
		items.forEach((item) => {
			item.classList.remove(
				"ring-2",
				"ring-[color:var(--accent-amber)]",
				"animate__animated",
				"animate__pulse"
			);
			item.style.opacity = "1";

			// Restaurar texto resaltado a normal
			const textos = item.querySelectorAll(".resaltado-busqueda");
			textos.forEach((t) => {
				const padre = t.parentNode;
				padre.textContent = padre.textContent; // Truco para eliminar el span
			});
		});

		if (query.length < 2) {
			actualizarContadorResultados(0);
			return;
		}

		items.forEach((item) => {
			// Buscar en múltiples campos
			const edpNum = item.querySelector(".font-bold")?.textContent || "";
			const proyecto = item.querySelector(".font-medium")?.textContent || "";
			const cliente = item.querySelectorAll("p.text-xs")[0]?.textContent || "";
			const jefeProyecto =
				item.querySelectorAll("p.text-xs")[1]?.textContent || "";
			const observaciones =
				item
					.querySelector("span[data-tooltip]")
					?.getAttribute("data-tooltip")
					?.replace("Obs: ", "") || "";

			// Búsqueda en todos los campos
			if (
				edpNum.toLowerCase().includes(query) ||
				proyecto.toLowerCase().includes(query) ||
				cliente.toLowerCase().includes(query) ||
				jefeProyecto.toLowerCase().includes(query) ||
				observaciones.toLowerCase().includes(query)
			) {
				// Destacar el item sin hacer scroll
				item.classList.add("ring-2", "ring-[color:var(--accent-amber)]");
				item.style.opacity = "1";
				coincidencias++;

				// Resaltar el texto específico que coincide
				resaltarCoincidencia(item, ".font-bold", query);
				resaltarCoincidencia(item, ".font-medium", query);
				resaltarCoincidencia(item, "p.text-xs", query);
			} else {
				// Reducir opacidad de los que no coinciden
				item.style.opacity = "0.5";
			}
		});

		actualizarContadorResultados(coincidencias);

		// Opcional: Mostrar botón "Ir al primer resultado" si hay resultados
		if (coincidencias > 0 && !document.getElementById("ir-primer-resultado")) {
			const boton = document.createElement("button");
			boton.id = "ir-primer-resultado";
			boton.className =
				"px-3 py-1 bg-[color:var(--bg-highlight)] text-xs rounded-md hover:bg-[color:var(--bg-card-hover)] transition-colors";
			boton.textContent = "Ir al primer resultado";
			boton.onclick = () => {
				const primerResultado = document.querySelector(".kanban-item.ring-2");
				if (primerResultado) {
					primerResultado.scrollIntoView({
						behavior: "smooth",
						block: "center",
					});
				}
			};
			resultadosContainer.appendChild(boton);
		} else if (coincidencias === 0) {
			const boton = document.getElementById("ir-primer-resultado");
			if (boton) boton.remove();
		}
	};

	// Función para resaltar coincidencias en el texto
	const resaltarCoincidencia = (item, selector, query) => {
		const elementos = item.querySelectorAll(selector);
		elementos.forEach((el) => {
			const texto = el.textContent;
			const indice = texto.toLowerCase().indexOf(query);

			if (indice >= 0) {
				const antes = texto.substring(0, indice);
				const coincidencia = texto.substring(indice, indice + query.length);
				const despues = texto.substring(indice + query.length);

				el.innerHTML = `${antes}<span class="resaltado-busqueda bg-yellow-100 text-yellow-800 px-0.5 rounded">${coincidencia}</span>${despues}`;
			}
		});
	};

	// Actualizar contador de resultados
	const actualizarContadorResultados = (cantidad) => {
		if (!resultadosContainer) return;

		if (cantidad > 0) {
			resultadosContainer.textContent = `${cantidad} resultado${
				cantidad > 1 ? "s" : ""
			} encontrado${cantidad > 1 ? "s" : ""}`;
			resultadosContainer.classList.remove("hidden");
		} else {
			resultadosContainer.textContent =
				inputBuscar.value.length >= 2 ? "No se encontraron resultados" : "";
			resultadosContainer.classList.toggle(
				"hidden",
				inputBuscar.value.length < 2
			);
		}
	};

	// Evento de entrada en el buscador
	inputBuscar.addEventListener("input", function () {
		buscarDebounced(this.value);
	});

	// Eventos de teclado para navegación
	inputBuscar.addEventListener("keydown", function (e) {
		if (e.key === "Enter") {
			e.preventDefault();

			const items = document.querySelectorAll(".kanban-item.ring-2");
			if (items.length === 0) return;

			// Si hay un item activo, ir al siguiente
			const activeItem = document.querySelector(
				".kanban-item.ring-2.active-search"
			);
			let nextItem;

			if (activeItem) {
				activeItem.classList.remove("active-search", "animate__pulse");
				const index = Array.from(items).indexOf(activeItem);
				nextItem = items[(index + 1) % items.length];
			} else {
				nextItem = items[0];
			}

			nextItem.classList.add(
				"active-search",
				"animate__animated",
				"animate__pulse"
			);
			nextItem.scrollIntoView({ behavior: "smooth", block: "center" });
		}

		// Atajo Escape para limpiar
		if (e.key === "Escape") {
			this.value = "";
			realizarBusqueda("");
			this.blur();
		}
	});

	// Evento de limpieza
	botonLimpiar.addEventListener("click", function () {
		inputBuscar.value = "";
		realizarBusqueda("");
		inputBuscar.focus();
	});

	// Teclas de acceso rápido globales
	document.addEventListener("keydown", function (e) {
		// Ctrl/Cmd + F para enfocar el buscador
		if ((e.ctrlKey || e.metaKey) && e.key === "f") {
			e.preventDefault();
			inputBuscar.focus();
			inputBuscar.select();
		}
	});
}

/**
 * INICIALIZACIÓN DEL KANBAN
 */
function resetCardPositions() {
	document.querySelectorAll(".kanban-item").forEach((item) => {
		// Resetear completamente todas las propiedades de posicionamiento
		item.style.cssText =
			"position: relative !important; left: 0 !important; margin: 0 !important; width: 100% !important;";
	});
}

function initKanbanBoard() {
	const columns = document.querySelectorAll(".kanban-column");

	// Ordenar inicialmente todas las columnas
	columns.forEach((col) => {
		ordenarTarjetasPorDias(col.querySelector(".kanban-list"));
	});

	columns.forEach((col) => {
		const estadoDestino = col.dataset.estado;
		const list = col.querySelector(".kanban-list");

		Sortable.create(list, {
			group: "edp-kanban",
			animation: 150,
			ghostClass: "sortable-ghost",
			chosenClass: "sortable-chosen",
			dragClass: "sortable-drag",
			fallbackClass: "sortable-fallback",
			fallbackOnBody: true,
			scrollSensitivity: 80,
			scrollSpeed: 10,

			// Agregar efectos visuales cuando comienza el arrastre
			onStart: function (evt) {
				document.body.classList.add("sorting");
				// Guardar posición de scroll y deshabilitar
				const lists = document.querySelectorAll(".kanban-list");
				lists.forEach((list) => {
					list._scrollTop = list.scrollTop; // Guardar posición
					list.classList.add("disable-scroll"); // Agregar clase para deshabilitar
				});

				// Crear un clon del elemento para mejor control
				const item = evt.item;
				const dragContainer = document.createElement("div");
				dragContainer.className = "drag-container";
				dragContainer.appendChild(item.cloneNode(true));
				document.body.appendChild(dragContainer);

				// Ajustar el ancho del elemento arrastrado para que coincida con el original
				const width = item.getBoundingClientRect().width;

				const fallback = document.querySelector(".sortable-fallback");
				if (fallback) {
					fallback.style.width = `${width}px`;
				}
				// Crear un efecto de "despegue" con destello
				item.classList.add("animate__animated", "animate__pulse");

				// Añadir un efecto de brillo alrededor de la tarjeta
				const glowEffect = document.createElement("div");
				glowEffect.className = "absolute inset-0 rounded-lg";
				glowEffect.style.boxShadow = "0 0 15px 5px rgba(59, 130, 246, 0.5)";
				glowEffect.style.animation = "glow 1s infinite alternate";
				glowEffect.style.pointerEvents = "none";
				glowEffect.style.zIndex = "-1";
				item.style.position = "relative";
				item.appendChild(glowEffect);

				// Aplicar un estilo CSS para destacar la tarjeta seleccionada
				item.style.zIndex = "10";
				item.style.transform = "scale(1.03) rotate(1deg)";
				item.style.boxShadow = "0 10px 25px -5px rgba(0, 0, 0, 0.2)";
				item.style.transition = "transform 0.2s ease, box-shadow 0.2s ease";
			},

			// Cuando termina el arrastre pero no hay cambio de columna
			onEnd: function (evt) {
				const dragContainer = document.querySelector(".drag-container");
				if (dragContainer) {
					document.body.removeChild(dragContainer);
				}
				document.body.classList.remove("sorting");

				// Restaurar scroll
				const lists = document.querySelectorAll(".kanban-list");
				lists.forEach((list) => {
					list.classList.remove("disable-scroll");
					if (list._scrollTop) {
						list.scrollTop = list._scrollTop; // Restaurar posición
					}
				});

				const item = evt.item;
				// Remover clase de animación
				item.classList.remove("animate__animated", "animate__pulse");

				// Eliminar efecto de brillo
				const glowEffect = item.querySelector(".absolute");
				if (glowEffect) {
					item.removeChild(glowEffect);
				}

				// Restaurar estilos originales con animación suave
				item.style.zIndex = "";
				item.style.transform = "";
				item.style.boxShadow = "";

				// Efecto de "aterrizaje" suave
				item.animate(
					[
						{ transform: "scale(1.05) translateY(-2px)" },
						{ transform: "scale(1) translateY(0)" },
					],
					{
						duration: 300,
						easing: "cubic-bezier(0.175, 0.885, 0.32, 1.275)",
					}
				);

				setTimeout(() => {
					item.style.position = "static";
					item.style.left = "auto";
					item.style.top = "auto";
					item.style.transform = "none";
				}, 10);
			},

			// Verificar si es permitido el movimiento
			onMove: function (evt) {
				// Código existente para onMove
				const estadoOrigen = evt.from.closest(".kanban-column").dataset.estado;
				const estadoDestino = evt.to.closest(".kanban-column").dataset.estado;

				// Regla de negocio: Restricción de Revisión a Validado
				if (
					estadoOrigen.toLowerCase() === "revision" &&
					estadoDestino.toLowerCase() === "validado"
				) {
					if (
						!confirm(
							"¿Estás seguro? Normalmente debes pasar por otro estado intermedio."
						)
					) {
						return false;
					}
				}

				return true;
			},

			// Al agregar un elemento a esta columna
			onAdd: function (evt) {
				const edpId = evt.item.dataset.id;
				const estadoOrigen = evt.from.closest(".kanban-column").dataset.estado;
				const estadoDestino = evt.to.closest(".kanban-column").dataset.estado;
				const item = evt.item;
				const fromList = evt.from;
				const toList = evt.to;

				// Limpiar efectos del arrastre
				item.classList.remove("animate__animated", "animate__pulse");
				const glowEffect = item.querySelector(".absolute");
				if (glowEffect) {
					item.removeChild(glowEffect);
				}

				// Determinar si necesitamos mostrar un modal basado en el estado destino
				let mostrarModal = false;
				let tipoModal = "";

				// Definir qué estados requieren confirmación con modal
				if (estadoDestino.toLowerCase() === "pagado") {
					mostrarModal = true;
					tipoModal = "confirmarPago";
				} else if (estadoDestino.toLowerCase() === "validado") {
					mostrarModal = true;
					tipoModal = "confirmarValidacion";
				} else if (
					estadoDestino.toLowerCase() === "revision" &&
					estadoOrigen.toLowerCase() === "enviado"
				) {
					mostrarModal = true;
					tipoModal = "revisionCliente";
				}

				// ACTUALIZACIÓN INMEDIATA: Actualizar el estado vacío/no-vacío y resumen
				const col = evt.to.closest(".kanban-column");
				const fromCol = evt.from.closest(".kanban-column");

				// Actualizar indicadores de columna origen y destino de inmediato
				col.setAttribute(
					"data-empty",
					col.querySelectorAll(".kanban-item").length === 0
				);
				fromCol.setAttribute(
					"data-empty",
					fromCol.querySelectorAll(".kanban-item").length === 0
				);
				actualizarContadoresTablero();

				// Preparar item para animación
				item.style.transition =
					"all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)";
				item.style.transform = "scale(1.08) translateY(-5px)";
				item.style.boxShadow = "0 15px 30px -10px rgba(0, 0, 0, 0.2)";
				item.style.zIndex = "5";

				if (mostrarModal) {
					fetch(`/controller/api/get-edp/${edpId}`)
						.then((response) => {
							if (!response.ok) {
								throw new Error(`Error al obtener datos: ${response.status}`);
							}
							return response.json();
						})
						.then((edpData) => {
							// Mostrar el modal contextual
							mostrarModalContextual(
								edpId,
								tipoModal,
								estadoOrigen,
								estadoDestino,
								edpData,
								(confirmado) => {
									if (confirmado) {
										// Continuar con la actualización normal
										actualizarEstadoEDP(
											edpId,
											estadoDestino,
											item,
											col,
											toList
										);
									} else {
										// Cancelado, devolver la tarjeta a su posición original
										fromList.appendChild(item);

										// Restaurar estilos
										item.style.transform = "scale(1)";
										item.style.boxShadow = "";
										item.style.zIndex = "";

										// Refrescar la UI
										actualizarContadoresTablero();
									}
								}
							);
						})
						.catch((error) => {
							console.error("Error al cargar datos del EDP:", error);
							// Si hay error, mostrar el modal sin datos
							mostrarModalContextual(
								edpId,
								tipoModal,
								estadoOrigen,
								estadoDestino,
								{},
								(confirmado) => {
									if (confirmado) {
										// Continuar con la actualización normal
										actualizarEstadoEDP(
											edpId,
											estadoDestino,
											item,
											col,
											toList
										);
									} else {
										// Cancelado, devolver la tarjeta a su posición original
										fromList.appendChild(item);

										// Restaurar estilos
										item.style.transform = "scale(1)";
										item.style.boxShadow = "";
										item.style.zIndex = "";

										// Refrescar la UI
										actualizarContadoresTablero();
									}
								}
							);
						});
				} else {
					// Variables para reglas de negocio
					let conformidadEnviada = false;

					// Aplicar reglas de negocio automáticas
					if (estadoDestino.toLowerCase() === "pagado") {
						conformidadEnviada = true;
						showToast(
							"Conformidad marcada como enviada automáticamente",
							"info"
						);
					}

					// Proceder normalmente para estados que no requieren modal
					actualizarEstadoEDP(
						edpId,
						estadoDestino,
						item,
						col,
						toList,
						conformidadEnviada
					);
				}
			},
		});
	});
}

// Reemplazar cualquier implementación existente con esta (igual a la del dashboard)
function openEdpModal(edpId) {
  console.log(`Abriendo modal para EDP ID: ${edpId}`);

  // Mostrar overlay y estado de carga
  const modalOverlay = document.getElementById('edpModalOverlay');
  const modalContent = document.getElementById('edpModalContent');
  
  if (!modalOverlay || !modalContent) {
    console.error('Error: Elementos del modal no encontrados');
    return;
  }
  
  modalOverlay.classList.remove('hidden');
  modalContent.innerHTML = `
    <div class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[color:var(--accent-blue)]"></div>
    </div>
  `;

  // URL actualizada para usar ID único
  fetch(`/controller/api/edp-details/${edpId}`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Datos recibidos correctamente:', data);
      // Renderizar contenido usando la función del otro archivo
      renderEdpModalContent(data);
    })
    .catch(error => {
      console.error('Error al cargar datos del EDP:', error);
      
      // Mostrar mensaje de error en el modal
      modalContent.innerHTML = `
        <div class="p-6 text-center">
          <div class="text-red-500 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="text-lg font-bold mb-2">Error al cargar datos</h3>
          <p>${error.message}</p>
          <div class="text-sm text-gray-500 mt-2 mb-4">
            Detalles técnicos: ${error}
          </div>
          <button type="button" id="closeModalError" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            Cerrar
          </button>
        </div>
      `;
      
      document.getElementById('closeModalError').addEventListener('click', function() {
        modalOverlay.classList.add('hidden');
      });
    });
}
/**
 * Función para actualizar estado en la API
 */
function actualizarEstadoEDP(
	edpId,
	estadoDestino,
	item,
	col,
	toList,
	conformidadEnviada = false
) {
	const loadingOverlay = document.createElement("div");
	loadingOverlay.className =
		"absolute inset-0 bg-black/20 rounded-lg flex items-center justify-center z-10";
	loadingOverlay.innerHTML = `
    <div class="bg-white/90 rounded-lg p-2 shadow-lg flex items-center">
      <svg class="animate-spin h-4 w-4 text-blue-500 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span class="text-xs font-medium">Actualizando...</span>
    </div>
  `;

	// Asegurarse de que la tarjeta tiene position relative para el overlay absoluto
	item.style.position = "relative";
	item.appendChild(loadingOverlay);
	// Enviar solicitud al servidor
	fetch("/controller/kanban/update_estado", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			"X-Requested-With": "XMLHttpRequest",
		},
		body: JSON.stringify({
			edp_id: edpId,
			nuevo_estado: estadoDestino,
			conformidad_enviada: conformidadEnviada,
		}),
	})
		.then((response) => {
			if (!response.ok) {
				throw new Error("Error en la respuesta del servidor");
			}
			return response.json();
		})
		.then((data) => {
			if (item.contains(loadingOverlay)) {
				item.removeChild(loadingOverlay);
			}
			// Éxito - animación de transición con ondas
			item.style.backgroundColor = "var(--accent-green)";
			item.style.color = "white";

			// Crear efecto de onda concéntrica
			const rippleEffect = document.createElement("div");
			rippleEffect.className = "absolute inset-0 rounded-lg";
			rippleEffect.style.border = "2px solid var(--accent-green)";
			rippleEffect.style.animation = "ripple 1s ease-out forwards";
			rippleEffect.style.pointerEvents = "none";
			item.appendChild(rippleEffect);

			// Animación de cambio de color
			item.animate(
				[
					{
						backgroundColor: "var(--bg-card)",
						boxShadow: "0 0 0 1px var(--accent-green)",
					},
					{
						backgroundColor: "var(--state-success-bg)",
						boxShadow: "0 0 15px rgba(16, 185, 129, 0.4)",
					},
					{
						backgroundColor: "var(--bg-card)",
						boxShadow: "0 0 0 1px var(--border-color)",
					},
				],
				{
					duration: 2500,
					easing: "cubic-bezier(0.4, 0, 0.2, 1)",
				}
			);

			actualizarContenidoTarjeta(item, data.edp_data || {}, estadoDestino);

			// Después restaurar y normalizar con una animación más elegante
			setTimeout(() => {
				// Eliminar el efecto de onda
				if (item.contains(rippleEffect)) {
					item.removeChild(rippleEffect);
				}

				// Transición de vuelta a normal
				item.animate(
					[
						{
							backgroundColor: "var(--accent-green)",
							color: "white",
							transform: "scale(1.08) translateY(-5px)",
						},
						{
							backgroundColor: "",
							color: "",
							transform: "scale(1) translateY(0)",
						},
					],
					{
						duration: 1500,
						easing: "cubic-bezier(0.4, 0, 0.2, 1)",
					}
				);

				// Restaurar estilos originales
				item.style.backgroundColor = "";
				item.style.color = "";
				item.style.transform = "scale(1)";
				item.style.boxShadow = "";
				item.style.zIndex = "";

				// Ordenar las tarjetas después de insertar
				setTimeout(() => {
					ordenarTarjetasPorDias(toList);

					// Actualizar columna vacía/no-vacía
					col.setAttribute(
						"data-empty",
						toList.querySelectorAll(".kanban-item").length === 0
					);

					// Actualizar resumen y totales de columnas
					updateSummaryPanel();
					calcularTotalesColumna();
					setupKPIPanel();
				}, 300);
			}, 600);

			showToast(`EDP-${edpId} movido a ${estadoDestino}`, "success");
		})
		.catch((error) => {
			console.error("Error:", error);

			// Error - hacer destello rojo y agitar
			item.style.backgroundColor = "var(--accent-red)";
			item.style.color = "white";

			// Efecto de agitación
			const shakeAnimation = [
				{ transform: "translateX(-5px)" },
				{ transform: "translateX(5px)" },
				{ transform: "translateX(-5px)" },
				{ transform: "translateX(5px)" },
				{ transform: "translateX(0)" },
			];

			item.animate(shakeAnimation, {
				duration: 500,
				iterations: 1,
			});

			// Restaurar
			setTimeout(() => {
				item.style.backgroundColor = "";
				item.style.color = "";
				item.style.boxShadow = "";
			}, 800);

			showToast(`Error al actualizar el estado`, "error");

			// Recargar para restaurar el estado
			setTimeout(() => location.reload(), 1500);
		});
}


/**
 * Muestra un modal contextual según el tipo de cambio de estado
 */
function mostrarModalContextual(
	edpId,
	tipoModal,
	estadoOrigen,
	estadoDestino,
	edpData,
	callback
) {
	// Crear overlay para el modal
	const overlay = document.createElement("div");
	overlay.className =
		"fixed inset-0 bg-black/60 backdrop-blur-sm z-[51] flex justify-center items-center animate__animated animate__fadeIn";

	// Contenido específico según el tipo de modal
	let contenidoHTML = "";
	let titulo = "";

	switch (tipoModal) {
		case "confirmarPago":
			titulo = "Confirmar Pago de EDP";
			contenidoHTML = `
        <div class="space-y-4">
          <p class="text-sm">Para marcar como pagado, confirma los siguientes datos:</p>
          
          <div class="form-group">
            <label class="form-label">Fecha de Pago</label>
            <input type="date" name="fecha_pago" class="form-input" required>
          </div>
          
          <div class="form-group">
            <label class="form-label">N° de Conformidad</label>
            <input type="text" name="n_conformidad" class="form-input" required>
          </div>
        </div>
      `;
			break;
		case "confirmarValidacion":
			titulo = "Confirmar Validación de EDP";
			contenidoHTML = `
        <div class="space-y-4">
          <p class="text-sm">Para validar el EDP, verifica que los siguientes datos sean correctos:</p>
          
          <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
            <div class="flex">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-sm text-yellow-700">
                  Revisa que estos datos estén correctos antes de validar el EDP.
                </p>
              </div>
            </div>
          </div>
          
          <!-- Verificación del N° de Conformidad -->
          <div class="form-group">
            <label class="form-label">N° de Conformidad</label>
            <div class="relative">
              <input type="text" name="n_conformidad" class="form-input pl-9" value="${
								edpData["N° Conformidad"] || ""
							}" required>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
          </div>
          
          <!-- Verificación de la Fecha de Conformidad -->
          <div class="form-group">
            <label class="form-label">Fecha de Conformidad</label>
            <div class="relative">
              <input type="date" name="fecha_conformidad" class="form-input pl-9" value="${formatFecha(
								edpData["Fecha Conformidad"] || ""
							)}" required>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          
          <!-- Fecha Estimada de Pago -->
          <div class="form-group">
            <label class="form-label">Fecha Estimada de Pago</label>
            <div class="relative">
              <input type="date" name="fecha_estimada_pago" class="form-input pl-9" value="${formatFecha(
								edpData["Fecha Estimada de Pago"] || ""
							)}" required>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          
          <div class="bg-blue-50 border-l-4 border-blue-400 p-4 mt-3">
            <div class="flex">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-sm text-blue-700">
                  Al validar se marcará automáticamente "Sí" en Conformidad Enviada y se registrará el usuario que realiza la acción.
                </p>
              </div>
            </div>
          </div>
        </div>
      `;
			break;

		case "revisionCliente":
			titulo = "EDP en Revisión por Cliente";
			contenidoHTML = `
        <div class="space-y-4">
          <p class="text-sm">Confirma los detalles de la revisión:</p>
          
          <div class="form-group">
            <label class="form-label">Contacto Cliente</label>
            <input type="text" name="contacto_cliente" class="form-input" required>
          </div>
          
          <div class="form-group">
            <label class="form-label">Fecha Estimada de Respuesta</label>
            <input type="date" name="fecha_estimada_respuesta" class="form-input" required>
          </div>
        </div>
      `;
			break;
	}

	// Estructura del modal
	overlay.innerHTML = `
    <div class="bg-[color:var(--bg-card)] rounded-xl shadow-2xl w-full max-w-md overflow-hidden flex flex-col animate__animated animate__zoomIn animate__faster">
      <div class="bg-gradient-to-r from-[color:var(--accent-blue-light)] to-[color:var(--accent-blue)] px-6 py-4 flex justify-between items-center">
        <h3 class="text-lg font-bold text-white">${titulo}</h3>
        <button id="cancelar-modal" class="text-white hover:bg-white/20 p-1.5 rounded-full transition-all">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <form id="modal-contextual-form" class="p-6">
        ${contenidoHTML}
        
        <div class="flex justify-end space-x-3 mt-6">
          <button type="button" id="cancelar-cambio" class="btn-secondary">
            Cancelar
          </button>
          <button type="submit" class="btn-primary flex items-center gap-1.5">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            Confirmar
          </button>
        </div>
      </form>
    </div>
  `;

	document.body.appendChild(overlay);

	// Configurar eventos
	document.getElementById("cancelar-modal").addEventListener("click", () => {
		cerrarModal(false);
	});

	document.getElementById("cancelar-cambio").addEventListener("click", () => {
		cerrarModal(false);
	});

	const form = document.getElementById("modal-contextual-form");
	form.addEventListener("submit", (e) => {
		e.preventDefault();

		// Mostrar estado de carga
		const submitButton = form.querySelector('button[type="submit"]');
		const cancelButton = document.getElementById("cancelar-cambio");

		// Guardar estado original del botón
		const originalHTML = submitButton.innerHTML;

		// Deshabilitar botones
		submitButton.disabled = true;
		cancelButton.disabled = true;

		// Cambiar aspecto del botón para mostrar que está procesando
		submitButton.innerHTML = `
    <div class="flex items-center">
      <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Guardando...
    </div>
  `;
		// Recoger datos del formulario
		const formData = new FormData(form);
		formData.append("edp_id", edpId);
		formData.append("nuevo_estado", estadoDestino);

		// Enviar datos al servidor
		fetch("/controller/kanban/update_estado_detallado", {
			method: "POST",
			body: formData,
		})
			.then((response) => response.json())
			.then((data) => {
				if (data.success) {
					showToast(`EDP-${edpId} actualizado correctamente`, "success");
					cerrarModal(true);
					submitButton.innerHTML = `
        <div class="flex items-center">
          <svg class="h-4 w-4 text-white mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          Guardado
        </div>
      `;
					// Esperar un momento para dar feedback visual antes de cerrar
					setTimeout(() => {
						showToast(`EDP-${edpId} actualizado correctamente`, "success");
						cerrarModal(true);
					}, 500);
				} else {
					throw new Error(data.message || "Error al actualizar");
				}
			})
			.catch((error) => {
				console.error("Error:", error);

				// Mostrar estado de error en el botón
				submitButton.innerHTML = `
      <div class="flex items-center">
        <svg class="h-4 w-4 text-white mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Error
      </div>
    `;
			});
		// Restaurar botones
		setTimeout(() => {
			submitButton.disabled = false;
			cancelButton.disabled = false;
			submitButton.innerHTML = originalHTML;
			showToast(`Error: ${error.message}`, "error");
		}, 1000);
	});

	function cerrarModal(confirmado) {
		overlay.classList.add("animate__fadeOut");
		overlay.querySelector("div").classList.add("animate__zoomOut");

		setTimeout(() => {
			document.body.removeChild(overlay);
			callback(confirmado);
		}, 300);
	}
}

/**
 * Configura la conexión con Socket.IO para actualizaciones en tiempo real
 */
function setupSocketConnection() {
	// Crear conexión
	const socket = io();

	// Gestionar estados de conexión
	socket.on("connect", () => {
		showToast("Conexión en tiempo real establecida", "info");
	});

	socket.on("disconnect", () => {
		showToast("Se perdió la conexión en tiempo real", "error");
	});

	// Escuchar actualizaciones
	socket.on("estado_actualizado", (data) => {
		// Destacar visualmente el cambio si se puede identificar la tarjeta
		if (data.edp_id) {
			const tarjeta = document.querySelector(
				`.kanban-item[data-id="${data.edp_id}"]`
			);
			if (tarjeta) {
				tarjeta.classList.add("highlight-update");
				setTimeout(() => tarjeta.classList.remove("highlight-update"), 2000);
			}
		}

		// Actualizar todos los contadores
		actualizarContadoresTablero();

		// Mostrar notificación
		showToast(`EDP actualizado: ${data.edp_id || "desconocido"}`, "info");
	});
}



