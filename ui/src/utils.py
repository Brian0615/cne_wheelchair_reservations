import math
from datetime import datetime, time

import pandas as pd
import streamlit as st
from plotly import graph_objects as go

from common.constants import DeviceStatus, Location, DeviceType
from common.data_models.device import Device


def display_inventory(device_type: DeviceType, inventory: pd.DataFrame):
    st.subheader(f"{device_type} Details")
    location_filter = st.selectbox(
        "Filter by Location",
        options=Location,
        index=None,
        key=f"{device_type.value.lower()}_location_filter",
    )
    if location_filter:
        inventory = inventory[inventory["location"] == location_filter]
    st.dataframe(
        data=inventory,
        column_order=["id", "status", "status"],
        column_config={
            "id": st.column_config.TextColumn(label=Device.model_fields["id"].title),
            "status": st.column_config.TextColumn(label=Device.model_fields["status"].title),
            "location": st.column_config.TextColumn(label=Device.model_fields["location"].title),
        },
        use_container_width=True,
        hide_index=True,
    )


def display_inventory_admin(device_type: str, inventory: pd.DataFrame):
    st.subheader(f"{device_type} Inventory")
    updated_inventory = st.data_editor(
        inventory.sort_values(by="id", ascending=True).reset_index(drop=True),
        column_order=["id", "status", "location"],
        column_config={
            "id": st.column_config.TextColumn(label=Device.model_fields["id"].title),
            "status": st.column_config.SelectboxColumn(
                label=Device.model_fields["status"].title,
                options=DeviceStatus,
                default=DeviceStatus.AVAILABLE,
            ),
            "location": st.column_config.SelectboxColumn(
                label=Device.model_fields["location"].title,
                options=Location,
                default=Location.BLC,
            ),
        },
        hide_index=True,
        num_rows="dynamic",
        use_container_width=True,
    )
    updated_inventory["type"] = device_type
    return updated_inventory


def load_reservations_for_date(date: datetime):
    reservations = pd.DataFrame(
        data={
            "name": ["Person A", "Person B", "Person C"],
            "phone_number": ["111-222-3333", "444-555-6666", "777-888-9999"],
            "location": ["BLC", "PG", "PG"],
            "reservation_time": [datetime.combine(date.date(), time(10, 15)) for _ in range(3)],
            "notes": ["", "", ""],
            "is_picked_up": [True, False, True],
            "time_out": [datetime.combine(date.date(), time(10, 15)), None, None],
            "time_in": [None, None, None],
        }
    )
    return reservations


def create_inventory_chart(inventory: pd.DataFrame):
    colour_mapping = {
        DeviceStatus.AVAILABLE: "#49994C",
        DeviceStatus.RENTED: "#E6920B",
        DeviceStatus.OUT_OF_SERVICE: "#D94936",
        DeviceStatus.BACKUP: "#A6A6A6"
    }
    fig = go.Figure()
    num_per_row = 25
    num_rows = math.ceil(len(inventory) / num_per_row)
    fig.update_layout(
        autosize=False,
        width=num_per_row * 50,
        height=70 * num_rows,
        margin={"l": 0, "r": 0, "b": 0, "t": 0, "pad": 0},
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )
    fig.update_xaxes(range=[0, num_per_row], visible=False, showgrid=False, zeroline=False)
    fig.update_yaxes(range=[-2 * num_rows, 0], visible=False, showgrid=False, zeroline=False)
    for i, (_, device) in enumerate(inventory.iterrows()):
        x0, y0, x1, y1 = (
            i % num_per_row,
            -2 * (i // num_per_row),
            (i % num_per_row) + 0.8,
            -2 * (i // num_per_row) - 1.8
        )
        fig.add_trace(
            go.Scatter(
                x=[x0, x0, x1, x1, x0],
                y=[y0, y1, y1, y0, y0],
                fill="toself",
                fillcolor=colour_mapping[device["status"]],
                line_color=colour_mapping[device["status"]],
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
                textfont={"color": "#EEEEEE", "size": 14},
                textposition="middle center",
                showlegend=False,
                hoverinfo="skip",
            )
        )
    return fig
