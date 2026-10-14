# -*- coding: utf-8 -*-
"""
MODUL: style_sheet.py
Fungsi: Definisi tema antarmuka QSS (Clean Modern Light Theme - Putih & Biru).
"""

LIGHT_THEME_QSS = """
    QWidget {
        background-color: #F0F7FF;
        font-family: 'Segoe UI', 'Ubuntu', sans-serif;
        color: #1E293B;
    }
    #HeaderCard {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
    }
    #PanelCard {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
    }
    #ConnNodeCard {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
    }
    #MainTitle {
        font-size: 16px;
        font-weight: 800;
        color: #0F172A;
    }
    #SubTitle {
        font-size: 14px;
        font-weight: bold;
        color: #2563EB;
    }
    #CardHeader {
        font-size: 13px;
        font-weight: bold;
        color: #1E293B;
    }
    #SubCardHeader {
        font-size: 12px;
        font-weight: bold;
        color: #334155;
    }
    #ButtonNameLabel {
        font-weight: bold;
        font-size: 12px;
        color: #334155;
    }
    #AnalogVal {
        font-weight: bold;
        font-size: 12px;
        color: #2563EB;
    }
    #StatName {
        color: #475569;
        font-size: 11px;
    }
    #StatVal {
        color: #0F172A;
        font-weight: 600;
        font-size: 11px;
    }
    #BadgeReleased {
        background-color: #F1F5F9;
        color: #64748B;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        font-size: 10px;
        font-weight: bold;
        padding: 3px 12px;
    }
    #BadgePressed {
        background-color: #2563EB;
        color: #FFFFFF;
        border: 1px solid #1D4ED8;
        border-radius: 10px;
        font-size: 10px;
        font-weight: bold;
        padding: 3px 12px;
    }
    #NodeBadgeConn {
        color: #16A34A;
        font-size: 10px;
        font-weight: bold;
    }
    #NodeBadgeDisconn {
        color: #DC2626;
        font-size: 10px;
        font-weight: bold;
    }
    #NodeBadgeWaiting {
        color: #94A3B8;
        font-size: 10px;
        font-weight: normal;
    }
    #BadgeStatusConn {
        background-color: #DCFCE7;
        color: #16A34A;
        border: 1px solid #86EFAC;
        border-radius: 8px;
        font-size: 10px;
        font-weight: bold;
        padding: 3px 10px;
    }
    #BadgeStatusDisconn {
        background-color: #FEE2E2;
        color: #DC2626;
        border: 1px solid #FCA5A5;
        border-radius: 8px;
        font-size: 10px;
        font-weight: bold;
        padding: 3px 10px;
    }
    #BadgeStatusWaiting {
        background-color: #F1F5F9;
        color: #94A3B8;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        font-size: 10px;
        font-weight: normal;
        padding: 3px 10px;
    }
    #BtnEstop {
        background-color: #EF4444;
        color: #FFFFFF;
        font-weight: bold;
        font-size: 11px;
        border-radius: 6px;
        padding: 5px 14px;
        border: 1px solid #DC2626;
    }
    #BtnEstop:hover {
        background-color: #DC2626;
    }
    #BtnSmall {
        background-color: #F8FAFC;
        color: #334155;
        border: 1px solid #CBD5E1;
        border-radius: 5px;
        font-size: 10px;
        padding: 3px 8px;
        font-weight: 600;
    }
    #BtnSmall:hover {
        background-color: #E2E8F0;
    }
    #InfoBox {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 6px;
    }
    #SerialConsole, #LogConsole {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 10px;
        color: #1E293B;
    }
    #ClockLabel {
        color: #64748B;
        font-size: 11px;
        font-weight: 600;
    }
"""
