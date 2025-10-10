const sources = [
  {
    id: "amiv-apero",
    label: "AMIV Aperos",
    path: "/data/apero_results_amiv.json",
  },
];

const MONTH_NAMES = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const calendarContainer = document.getElementById("calendar");
const eventPanel = document.getElementById("event-panel");

const state = {
  events: [],
  eventsByDay: new Map(),
  month: new Date().getMonth(),
  year: new Date().getFullYear(),
  activeDay: null,
};

const toISODate = (date) => date.toISOString().slice(0, 10);

const formatDisplayDate = (isoString) =>
  new Date(`${isoString}T00:00:00`).toLocaleDateString(undefined, {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

const formatEventTime = (event) => {
  if (event.startTime && event.endTime) {
    return `${event.startTime} — ${event.endTime}`;
  }
  return event.startTime || event.endTime || null;
};

const normaliseEntry = (entry, sourceId) => {
  if (!entry?.date) {
    throw new Error(`Missing date in ${sourceId} entry: ${JSON.stringify(entry)}`);
  }

  return {
    id: `${sourceId}-${entry.id ?? `${entry.title ?? "event"}-${entry.date}`}`,
    title: entry.title ?? "Untitled event",
    date: entry.date,
    startTime: entry.start_time ?? entry.startTime ?? null,
    endTime: entry.end_time ?? entry.endTime ?? null,
    location: entry.location ?? null,
    url: entry.url ?? null,
    source: sourceId,
    raw: entry,
  };
};

const fetchJson = async (source) => {
  const response = await fetch(source.path);
  if (!response.ok) {
    throw new Error(`Failed to load ${source.path}: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

const loadEventSources = async () => {
  const items = [];

  for (const source of sources) {
    const payload = await fetchJson(source);
    const list = Array.isArray(payload) ? payload : [payload];

    let skipped = 0;
    list.forEach((entry, idx) => {
      if (!entry || !entry.date) {
        skipped += 1;
        return;
      }
      const event = normaliseEntry(entry, source.id);
      items.push(event);
    });

    if (skipped > 0) {
      // Surface a clear hint in devtools without interrupting the UI
      console.warn(`Skipped ${skipped} invalid entries from ${source.id} (missing date).`);
    }
  }

  return items;
};

const createEventLookup = (events) => {
  const map = new Map();

  events.forEach((event) => {
    if (!event.date) {
      return;
    }

    const iso = event.date.length === 10 ? event.date : event.date.slice(0, 10);

    if (!map.has(iso)) {
      map.set(iso, []);
    }

    map.get(iso).push(event);
  });

  for (const list of map.values()) {
    list.sort((a, b) => {
      if (a.startTime && b.startTime) {
        return a.startTime.localeCompare(b.startTime);
      }
      if (a.startTime) {
        return -1;
      }
      if (b.startTime) {
        return 1;
      }
      return a.title.localeCompare(b.title);
    });
  }

  return map;
};

const buildCalendarMatrix = (year, month) => {
  const firstDay = new Date(Date.UTC(year, month, 1));
  const startOffset = (firstDay.getUTCDay() + 6) % 7;
  const daysInMonth = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();

  const weeks = [];
  let dayCounter = 1 - startOffset;

  for (let week = 0; week < 6; week += 1) {
    const days = [];

    for (let weekday = 0; weekday < 7; weekday += 1) {
      const date = new Date(Date.UTC(year, month, dayCounter));
      const inMonth = date.getUTCMonth() === month;
      days.push({ date, inMonth });
      dayCounter += 1;
    }

    weeks.push(days);

    if (dayCounter > daysInMonth && days.every((day) => day.date.getUTCMonth() !== month)) {
      break;
    }
  }

  return weeks;
};

const showStatus = (type, message) => {
  const className = type === "error" ? "error-notice" : "loading-notice";
  calendarContainer.innerHTML = `<div class="${className}">${message}</div>`;
};

const renderCalendar = () => {
  const { year, month, eventsByDay, activeDay, events } = state;

  calendarContainer.innerHTML = "";

  const calendar = document.createElement("div");
  calendar.className = "calendar";

  const heading = document.createElement("div");
  heading.className = "calendar__heading";

  const title = document.createElement("h2");
  title.textContent = `${MONTH_NAMES[month]} ${year}`;

  const meta = document.createElement("p");
  meta.textContent = `${events.length} event${events.length === 1 ? "" : "s"} loaded`;

  heading.append(title, meta);

  const grid = document.createElement("div");
  grid.className = "calendar__grid";

  WEEKDAYS.forEach((weekday) => {
    const label = document.createElement("div");
    label.className = "calendar__weekday";
    label.textContent = weekday;
    grid.appendChild(label);
  });

  const weeks = buildCalendarMatrix(year, month);

  weeks.forEach((week) => {
    week.forEach(({ date, inMonth }) => {
      const iso = toISODate(date);
      const dayEvents = eventsByDay.get(iso) ?? [];

      const button = document.createElement("button");
      button.type = "button";
      button.className = "calendar__day";
      button.dataset.day = iso;

      if (!inMonth) {
        button.classList.add("calendar__day--muted");
      }

      if (dayEvents.length > 0) {
        button.classList.add("calendar__day--highlight");
      }

      if (activeDay === iso) {
        button.classList.add("calendar__day--active");
      }

      const dateLabel = document.createElement("span");
      dateLabel.className = "calendar__date";
      dateLabel.textContent = date.getUTCDate();

      const eventsContainer = document.createElement("div");
      eventsContainer.className = "calendar__events";

      dayEvents.slice(0, 3).forEach((event) => {
        const chip = document.createElement("span");
        chip.className = "calendar__event-chip";
        chip.textContent = event.title;
        eventsContainer.appendChild(chip);
      });

      if (dayEvents.length > 3) {
        const more = document.createElement("span");
        more.className = "calendar__more";
        more.textContent = `+${dayEvents.length - 3}`;
        eventsContainer.appendChild(more);
      }

      button.append(dateLabel, eventsContainer);

      button.addEventListener("click", () => setActiveDay(iso));
      button.addEventListener("keypress", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          setActiveDay(iso);
        }
      });

      grid.appendChild(button);
    });
  });

  calendar.append(heading, grid);
  calendarContainer.appendChild(calendar);
};

const renderEventPanel = () => {
  const { activeDay, eventsByDay } = state;

  if (!activeDay) {
    eventPanel.innerHTML = `
      <div class="event-panel__placeholder">
        <h2>Select a highlighted day</h2>
        <p>Day details appear here so you can plan your visit.</p>
      </div>
    `;
    eventPanel.classList.add("event-panel--empty");
    return;
  }

  const dayEvents = eventsByDay.get(activeDay) ?? [];

  if (dayEvents.length === 0) {
    eventPanel.innerHTML = `
      <div class="event-panel__placeholder">
        <h2>${formatDisplayDate(activeDay)}</h2>
        <p>No aperos scheduled for this day yet.</p>
      </div>
    `;
    eventPanel.classList.add("event-panel--empty");
    return;
  }

  eventPanel.classList.remove("event-panel--empty");
  eventPanel.innerHTML = "";

  const header = document.createElement("div");
  header.className = "event-panel__header";

  const title = document.createElement("h2");
  title.textContent = formatDisplayDate(activeDay);

  const counter = document.createElement("span");
  counter.textContent = `${dayEvents.length} event${dayEvents.length === 1 ? "" : "s"}`;

  header.append(title, counter);

  const list = document.createElement("ul");
  list.className = "event-panel__list";

  dayEvents.forEach((event) => {
    const item = document.createElement("li");

    const card = document.createElement("article");
    card.className = "event-card";

    const source = document.createElement("span");
    source.className = "event-card__source";
    source.textContent = event.source.replace(/[-_]/g, " ").toUpperCase();

    const eventTitle = document.createElement("span");
    eventTitle.className = "event-card__title";
    eventTitle.textContent = event.title;

    const metaLines = [];
    const time = formatEventTime(event);
    if (time) {
      metaLines.push(time);
    }
    if (event.location) {
      metaLines.push(event.location);
    }

    const url =
      event.url && event.url.startsWith("http")
        ? event.url
        : event.url
        ? `https://amiv.ethz.ch/${event.url.replace(/^\/+/, "")}`
        : null;

    card.append(source, eventTitle);

    if (metaLines.length > 0) {
      const meta = document.createElement("span");
      meta.className = "event-card__meta";
      meta.textContent = metaLines.join(" · ");
      card.appendChild(meta);
    }

    if (metaLines.length === 0) {
      const spacer = document.createElement("span");
      spacer.className = "event-card__meta";
      spacer.textContent = "Details coming soon";
      card.appendChild(spacer);
    }

    if (url) {
      const link = document.createElement("a");
      link.className = "event-card__link";
      link.href = url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = "View event";
      card.appendChild(link);
    }

    item.appendChild(card);
    list.appendChild(item);
  });

  eventPanel.append(header, list);
};

const setActiveDay = (isoString) => {
  state.activeDay = isoString;
  renderCalendar();
  renderEventPanel();
};

const initialise = async () => {
  try {
    showStatus("loading", "Loading events…");
    const events = await loadEventSources();

    state.events = events;
    state.eventsByDay = createEventLookup(events);

    const todayIso = toISODate(new Date());
    const eventDays = Array.from(state.eventsByDay.keys()).sort();
    const preferredDay = eventDays.includes(todayIso)
      ? todayIso
      : eventDays.find((iso) => iso.startsWith(`${state.year}-`)) ?? eventDays[0] ?? null;

    state.activeDay = preferredDay ?? null;

    renderCalendar();
    renderEventPanel();
  } catch (error) {
    console.error(error);
    showStatus("error", "Couldn't load events just now. Please verify the JSON files in data/.");
    eventPanel.innerHTML = `
      <div class="event-panel__placeholder">
        <h2>No events available</h2>
        <p>Check that <code>data/apero_results_amiv.json</code> exists and is valid JSON.</p>
      </div>
    `;
    eventPanel.classList.add("event-panel--empty");
  }
};

initialise();
