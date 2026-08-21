import itertools
import math
from functools import wraps
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st
from plotly import graph_objects as go

from common.constants import DeviceType, DeviceStatus, Location
from common.data_models import NewDevice
from common.cne_dates import CNEDates
from ui.src.data_service import DataService

_TRANSPARENT_BACKGROUND = "rgba(0, 0, 0, 0)"


def get_manage_devices_str(action: str, device_type: DeviceType, num_devices: int) -> str:
    """Get the string for labelling UI components related to managing devices"""
    return f"{action.title()} {num_devices} {device_type.value}{'s' if abs(num_devices) != 1 else ''}"


def display_devices_multiselect(inventory: pd.DataFrame, device_type: DeviceType, action: str) -> Tuple[List[str], str]:
    """Display a multiselect widget to select devices for management actions."""
    selected_devices = st.multiselect(
        f"{device_type}s to {action.title()}",
        options=sorted(inventory["id"].tolist()),
        default=None,
        key=f"{device_type.value.lower()}_to_{action.lower()}",
    )
    label = get_manage_devices_str(action=action, device_type=device_type, num_devices=len(selected_devices))
    return selected_devices, label


def display_toast_on_success(func):
    """Decorator to display a toast message on successful device management actions."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result is None:
            return
        status_code, response, success_msg = result
        if status_code == 200:
            st.session_state["manage_inventory_toast_msg"] = f"**Success!** {success_msg}"
            st.rerun()
        else:
            st.error(response)

    return wrapper


@display_toast_on_success
def add_devices(data_service: DataService, device_type: DeviceType):
    """Add devices to the inventory."""

    num_to_add = {}
    cols = st.columns(len(Location))
    for col, location in zip(cols, Location):
        num_to_add[location] = col.number_input(
            f"Number of {device_type}s to add at **{location}**",
            min_value=0,
            max_value=50,
            value=0,
            step=1,
        )

    label = get_manage_devices_str(action="add", device_type=device_type, num_devices=sum(num_to_add.values()))
    if st.button(label=label, disabled=sum(num_to_add.values()) < 1):
        new_devices = itertools.chain.from_iterable(
            [
                NewDevice(
                    cne_year=CNEDates.get_cne_year(),
                    type=device_type,
                    status=DeviceStatus.AVAILABLE,
                    location=Location(location),
                )
            ] * num_to_add_at_location
            for location, num_to_add_at_location in num_to_add.items()
        )

        status_code, result = data_service.add_devices(devices=new_devices)
        return status_code, result, f"{label.replace('Add', 'Added')} to the inventory"
    return None


@display_toast_on_success
def update_devices(data_service: DataService, device_type: DeviceType, inventory: pd.DataFrame):
    """Update device status in the inventory."""
    device_ids, label = display_devices_multiselect(inventory=inventory, device_type=device_type, action="update")
    new_status = st.pills(
        label="New Status",
        options=DeviceStatus,
        default=None,
        selection_mode="single",
        width="stretch",
        key=f"{device_type.value.lower()}_new_status",
    )

    if st.button(label=label, disabled=(not device_ids or not new_status)):
        status_code, result = data_service.update_devices_status(device_ids=device_ids, status=new_status)
        return status_code, result, f"{label.replace('Update', 'Updated')} to {new_status}"
    return None


@display_toast_on_success
def transfer_devices(data_service: DataService, device_type: DeviceType, inventory: pd.DataFrame):
    """Transfer devices to a new location."""
    device_ids, label = display_devices_multiselect(inventory=inventory, device_type=device_type, action="transfer")
    new_location = st.pills(
        label="New Location",
        options=Location,
        default=None,
        selection_mode="single",
        width="stretch",
        key=f"{device_type.value.lower()}_new_location",
    )

    if st.button(label=label, disabled=(not device_ids or not new_location)):
        status_code, result = data_service.update_devices_location(device_ids=device_ids, location=new_location)
        return status_code, result, f"{label.replace('Transfer', 'Transferred')} to {new_location}"
    return None


@display_toast_on_success
def remove_devices(data_service: DataService, device_type: DeviceType, inventory: pd.DataFrame):
    """Remove devices from the inventory."""
    device_ids, label = display_devices_multiselect(inventory=inventory, device_type=device_type, action="remove")
    if device_ids:
        st.warning("**Note**: This action cannot be undone!")

    if st.button(label=label, disabled=not device_ids):
        status_code, result = data_service.remove_devices(device_ids=device_ids)
        return status_code, result, f"{label.replace('Remove', 'Removed')} from the inventory"
    return None


def _add_device_status_cell(
        fig: go.Figure, bbox: Tuple[float, float, float, float], device: pd.Series, font_size: int = 14
):
    """Add a coloured cell (status-filled rectangle + centered ID label) to a chart at the given
    (x0, y0, x1, y1) bounding box. Shared by create_inventory_chart and create_dashboard_inventory_chart
    so both charts render device cells identically, aside from the dashboard's larger font_size.
    """
    x0, y0, x1, y1 = bbox
    colour = DeviceStatus.get_device_status_colour(device["status"])
    fig.add_trace(
        go.Scatter(
            x=[x0, x0, x1, x1, x0],
            y=[y0, y1, y1, y0, y0],
            fill="toself",
            fillcolor=colour,
            line_color=colour,
            mode="lines",
            text=f"<b>{device['id']}</b><br>Status: {device['status']}<br>Location: {device['location']}",
            hoverinfo="text",
            hoverlabel={"font_size": 14},
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[(x0 + x1) / 2.0],
            y=[(y0 + y1) / 2.0],
            mode="text",
            text=device["id"],
            textfont={"color": "#EEEEEE", "size": font_size},
            textposition="middle center",
            showlegend=False,
            hoverinfo="skip",
        )
    )


# noinspection PyTypeChecker
def create_inventory_chart(inventory: pd.DataFrame):
    """Create a chart to display the inventory."""

    fig = go.Figure()
    num_per_row = 25
    num_rows = math.ceil(len(inventory) / num_per_row)
    fig.update_layout(
        autosize=False,
        width=num_per_row * 50,
        height=35 * num_rows,
        margin={"l": 0, "r": 0, "b": 0, "t": 0, "pad": 0},
        plot_bgcolor=_TRANSPARENT_BACKGROUND,
        paper_bgcolor=_TRANSPARENT_BACKGROUND,
    )
    fig.update_xaxes(range=[0, num_per_row], visible=False, showgrid=False, zeroline=False)
    fig.update_yaxes(range=[-2 * num_rows, 0], visible=False, showgrid=False, zeroline=False)
    for i, (_, device) in enumerate(inventory.iterrows()):
        bbox = (
            i % num_per_row,
            -2 * (i // num_per_row),
            (i % num_per_row) + 0.8,
            -2 * (i // num_per_row) - 1.5
        )
        _add_device_status_cell(fig, bbox, device)
    return fig


_DASHBOARD_CHART_MAX_ROWS = 8
_DASHBOARD_CHART_LOCATIONS: List[Location] = list(Location)
# Larger than create_inventory_chart's default font size (14) since the Inventory Dashboard's charts
# have more room to breathe and benefit from being readable at a glance.
_DASHBOARD_CHART_FONT_SIZE = 24
# Horizontal gap (in column-width units) between two wrapped columns of the *same* location, kept
# small so they read as one continuous group rather than separate blocks.
_DASHBOARD_CHART_COLUMN_GAP = 0.1
# Horizontal gap between the last column of one location and the first column of the next, kept
# larger than _DASHBOARD_CHART_COLUMN_GAP so BLC and PG read as visually distinct blocks.
_DASHBOARD_CHART_LOCATION_GAP = 0.4


def _dashboard_chart_location_column_counts(inventory: pd.DataFrame) -> Dict[Location, int]:
    """Get the number of columns each location needs (in _DASHBOARD_CHART_LOCATIONS order), each
    wrapping every _DASHBOARD_CHART_MAX_ROWS devices. Every location gets at least one column, even
    if it has no devices, so its header is always shown and it never has to share a column with
    another location -- e.g. if BLC doesn't fill its last column, PG still starts a new one.
    """
    return {
        location: max(1, math.ceil(int((inventory["location"] == location).sum()) / _DASHBOARD_CHART_MAX_ROWS))
        for location in _DASHBOARD_CHART_LOCATIONS
    }


def _dashboard_chart_column_starts(location_column_counts: Dict[Location, int]) -> Dict[Location, int]:
    """Get the starting column index for each location, placed one after another in
    _DASHBOARD_CHART_LOCATIONS order so locations are never interleaved or share a column."""
    starts = {}
    offset = 0
    for location in _DASHBOARD_CHART_LOCATIONS:
        starts[location] = offset
        offset += location_column_counts[location]
    return starts


def _dashboard_chart_column_x_starts(location_column_counts: Dict[Location, int]) -> List[float]:
    """Get the x-axis start position for every column, in order: columns wrapped within the same
    location are spaced by the small _DASHBOARD_CHART_COLUMN_GAP, while the first column of a new
    location is spaced by the larger _DASHBOARD_CHART_LOCATION_GAP, so locations read as distinct
    blocks even though a location's own wrapped columns read as one group."""
    x_starts: List[float] = []
    x = 0.0
    for location in _DASHBOARD_CHART_LOCATIONS:
        for block in range(location_column_counts[location]):
            if x_starts:
                gap = _DASHBOARD_CHART_COLUMN_GAP if block > 0 else _DASHBOARD_CHART_LOCATION_GAP
                x += 1 + gap
            x_starts.append(x)
    return x_starts


def _dashboard_chart_cell_bbox(x_start: float, row_index: int) -> Tuple[float, float, float, float]:
    """Get the (x0, y0, x1, y1) bounding box for a dashboard chart cell at the given column/row."""
    y0 = -2 * (row_index + 1)
    return x_start, y0, x_start + 0.8, y0 - 1.5


def _add_dashboard_chart_column_headers(
        fig: go.Figure,
        location_column_counts: Dict[Location, int],
        column_starts: Dict[Location, int],
        column_x_starts: List[float],
):
    """Add the location label above each column of the dashboard chart."""
    for location in _DASHBOARD_CHART_LOCATIONS:
        for block in range(location_column_counts[location]):
            x_start = column_x_starts[column_starts[location] + block]
            fig.add_trace(
                go.Scatter(
                    x=[x_start + 0.4],
                    y=[-0.5],
                    mode="text",
                    text=f"<b>{location}</b>",
                    textfont={"size": _DASHBOARD_CHART_FONT_SIZE},
                    showlegend=False,
                    hoverinfo="skip",
                )
            )


def _add_dashboard_chart_location_dividers(
        fig: go.Figure,
        location_column_counts: Dict[Location, int],
        column_starts: Dict[Location, int],
        column_x_starts: List[float],
):
    """Draw a vertical divider line between each pair of adjacent locations' columns, midway
    through the larger cross-location gap, so BLC and PG read as clearly separate blocks."""
    for previous_location, next_location in itertools.pairwise(_DASHBOARD_CHART_LOCATIONS):
        previous_last_col = column_starts[previous_location] + location_column_counts[previous_location] - 1
        previous_end = column_x_starts[previous_last_col] + 0.8
        next_start = column_x_starts[column_starts[next_location]]
        fig.add_vline(
            x=(previous_end + next_start) / 2.0,
            line={"color": "rgba(128, 128, 128, 0.4)", "width": 2},
        )


def get_dashboard_chart_column_weight(inventory: pd.DataFrame) -> int:
    """Get the number of columns create_dashboard_inventory_chart will need for this inventory.

    Since the chart wraps into a new column every _DASHBOARD_CHART_MAX_ROWS devices per location,
    this tracks the chart's actual rendered width (unlike a raw device count) -- e.g. 11 devices at
    one location need 2 columns (same width as up to 20), not marginally more than 9 devices' single
    column. An empty inventory renders no chart at all (just a caption), so it weighs the minimum.
    Intended for weighting st.columns(...) so multiple dashboard charts share space proportionally
    to how wide they'll actually render, rather than by raw device count.
    """
    if inventory.empty:
        return 1
    return sum(_dashboard_chart_location_column_counts(inventory).values())


# noinspection PyTypeChecker
def create_dashboard_inventory_chart(inventory: pd.DataFrame):
    """Create a chart for the Inventory Dashboard: each location (BLC, PG) gets its own dedicated
    set of columns, with that location's devices listed in ID order, one row per device (up to
    _DASHBOARD_CHART_MAX_ROWS), wrapping into an additional column of its own once it has more
    devices than fit in one. Locations are placed one after another left-to-right and never share a
    column -- e.g. if BLC doesn't fill its last column, PG still starts a new one.
    """
    location_column_counts = _dashboard_chart_location_column_counts(inventory)
    column_starts = _dashboard_chart_column_starts(location_column_counts)
    column_x_starts = _dashboard_chart_column_x_starts(location_column_counts)
    # the last column's start plus its own 1-unit width (0.8 filled + 0.2 trailing padding).
    chart_width_units = column_x_starts[-1] + 1

    fig = go.Figure()
    fig.update_layout(
        autosize=False,
        width=int(chart_width_units * 90),
        height=50 * (_DASHBOARD_CHART_MAX_ROWS + 1),
        margin={"l": 0, "r": 0, "b": 0, "t": 0, "pad": 0},
        plot_bgcolor=_TRANSPARENT_BACKGROUND,
        paper_bgcolor=_TRANSPARENT_BACKGROUND,
    )
    fig.update_xaxes(range=[0, chart_width_units], visible=False, showgrid=False, zeroline=False)
    fig.update_yaxes(
        range=[-2 * (_DASHBOARD_CHART_MAX_ROWS + 1), 0], visible=False, showgrid=False, zeroline=False
    )

    _add_dashboard_chart_column_headers(fig, location_column_counts, column_starts, column_x_starts)
    _add_dashboard_chart_location_dividers(fig, location_column_counts, column_starts, column_x_starts)

    for location in _DASHBOARD_CHART_LOCATIONS:
        location_inventory = inventory[inventory["location"] == location].sort_values("id").reset_index(drop=True)
        for i, (_, device) in enumerate(location_inventory.iterrows()):
            block, row_index = divmod(i, _DASHBOARD_CHART_MAX_ROWS)
            col_index = column_starts[location] + block
            bbox = _dashboard_chart_cell_bbox(column_x_starts[col_index], row_index)
            _add_device_status_cell(fig, bbox, device, font_size=_DASHBOARD_CHART_FONT_SIZE)
    return fig


# noinspection PyTypeChecker
def create_dashboard_legend_chart():
    """Create a Plotly legend mapping each DeviceStatus to its colour, using the same coloured-cell
    style as create_dashboard_inventory_chart so the two visually match."""
    statuses = list(DeviceStatus)

    fig = go.Figure()
    fig.update_layout(
        autosize=False,
        width=210 * len(statuses),
        height=40,
        margin={"l": 0, "r": 0, "b": 0, "t": 0, "pad": 0},
        plot_bgcolor=_TRANSPARENT_BACKGROUND,
        paper_bgcolor=_TRANSPARENT_BACKGROUND,
    )
    fig.update_xaxes(range=[0, len(statuses)], visible=False, showgrid=False, zeroline=False)
    fig.update_yaxes(range=[-1.5, 0], visible=False, showgrid=False, zeroline=False)

    for i, status in enumerate(statuses):
        x0, y0, x1, y1 = i + 0.1, -0.3, i + 0.3, -1.2
        colour = DeviceStatus.get_device_status_colour(status)
        fig.add_trace(
            go.Scatter(
                x=[x0, x0, x1, x1, x0],
                y=[y0, y1, y1, y0, y0],
                fill="toself",
                fillcolor=colour,
                line_color=colour,
                mode="lines",
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[x1 + 0.15],
                y=[(y0 + y1) / 2.0],
                mode="text",
                text=status,
                textfont={"size": _DASHBOARD_CHART_FONT_SIZE},
                textposition="middle right",
                showlegend=False,
                hoverinfo="skip",
            )
        )
    return fig
