"""PDF generator service for creating scouting reports."""
import os
import tempfile
from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime
import io

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch

from app.core.config import settings
from app.core.logging import logger
from app.models.report import Report


class PDFGeneratorService:
    """Service for generating PDF scouting reports."""

    async def generate_pdf(self, analysis_results: Dict[str, Any], report: Report) -> str:
        """
        Generate a PDF scouting report.

        Args:
            analysis_results: Analysis results from video analysis
            report: Report database object

        Returns:
            Path to the generated PDF file
        """
        logger.info(f"Generating PDF for report ID: {report.id}")

        # Create a directory for reports if it doesn't exist
        reports_dir = os.path.join(tempfile.gettempdir(), "scouting_reports")
        os.makedirs(reports_dir, exist_ok=True)

        # Create the PDF filename
        pdf_filename = f"scouting_report_{report.id}_{int(datetime.now().timestamp())}.pdf"
        pdf_path = os.path.join(reports_dir, pdf_filename)

        # Generate the PDF content
        try:
            # Create the PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )

            # Get styles
            styles = getSampleStyleSheet()
            title_style = styles['Title']
            heading_style = styles['Heading1']
            subheading_style = styles['Heading2']
            normal_style = styles['Normal']

            # Create custom styles
            team_name_style = ParagraphStyle(
                'TeamName',
                parent=styles['Title'],
                fontSize=16,
                textColor=colors.darkblue
            )

            player_name_style = ParagraphStyle(
                'PlayerName',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.darkblue
            )

            # Build the document content
            content = []

            # Add title
            content.append(Paragraph(f"Scouting Report: {report.title}", title_style))
            content.append(Spacer(1, 0.25 * inch))

            # Add report metadata
            content.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", normal_style))
            if report.team_name:
                content.append(Paragraph(f"Team: {report.team_name}", normal_style))
            if report.opponent_name:
                content.append(Paragraph(f"Opponent: {report.opponent_name}", normal_style))
            if report.game_date:
                content.append(Paragraph(f"Game Date: {report.game_date.strftime('%Y-%m-%d')}", normal_style))
            content.append(Spacer(1, 0.5 * inch))

            # Add team analysis section if available
            team_analysis = analysis_results.get('team_analysis', {})
            if team_analysis:
                content.append(Paragraph("Team Analysis", heading_style))
                content.append(Spacer(1, 0.25 * inch))

                # Team name
                team_name = team_analysis.get('team_name', 'Unknown Team')
                content.append(Paragraph(f"{team_name}", team_name_style))
                content.append(Spacer(1, 0.15 * inch))

                # Team strengths and weaknesses
                strengths = team_analysis.get('team_strengths', [])
                if strengths:
                    content.append(Paragraph("Team Strengths:", subheading_style))
                    for strength in strengths:
                        content.append(Paragraph(f"• {strength}", normal_style))
                    content.append(Spacer(1, 0.15 * inch))

                weaknesses = team_analysis.get('team_weaknesses', [])
                if weaknesses:
                    content.append(Paragraph("Team Weaknesses:", subheading_style))
                    for weakness in weaknesses:
                        content.append(Paragraph(f"• {weakness}", normal_style))
                    content.append(Spacer(1, 0.15 * inch))

                # Recommended strategy
                strategy = team_analysis.get('recommended_strategy')
                if strategy:
                    content.append(Paragraph("Recommended Strategy:", subheading_style))
                    content.append(Paragraph(strategy, normal_style))
                    content.append(Spacer(1, 0.25 * inch))

                # Player analysis
                players = team_analysis.get('players', [])
                if players:
                    content.append(Paragraph("Player Analysis", heading_style))
                    content.append(Spacer(1, 0.25 * inch))

                    for player in players:
                        # Highlight the jersey number prominently
                        jersey_number = player.get('jersey_number', 'N/A')
                        player_name = player.get('name', f"Player #{jersey_number}")
                        position = player.get('position', 'Unknown')

                        content.append(Paragraph(f"#{jersey_number} - {player_name} ({position})", player_name_style))

                        # Player attributes table
                        data = []

                        # Physical attributes
                        physical = player.get('physical_attributes', {})
                        if physical:
                            data.append(['Physical Attributes', 'Rating (1-10)'])
                            for attr, value in physical.items():
                                data.append([attr.replace('_', ' ').title(), str(value)])

                        # Create the table
                        if data:
                            table = Table(data, colWidths=[3*inch, 1*inch])
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                                ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)
                            ]))
                            content.append(table)
                            content.append(Spacer(1, 0.15 * inch))

                        # Player strengths and weaknesses
                        strengths = player.get('strengths', [])
                        if strengths:
                            content.append(Paragraph("Strengths:", subheading_style))
                            for strength in strengths:
                                content.append(Paragraph(f"• {strength}", normal_style))
                            content.append(Spacer(1, 0.15 * inch))

                        weaknesses = player.get('weaknesses', [])
                        if weaknesses:
                            content.append(Paragraph("Weaknesses:", subheading_style))
                            for weakness in weaknesses:
                                content.append(Paragraph(f"• {weakness}", normal_style))
                            content.append(Spacer(1, 0.15 * inch))

                        # Strategy notes
                        strategy_notes = player.get('strategy_notes')
                        if strategy_notes:
                            content.append(Paragraph("Strategy Notes:", subheading_style))
                            content.append(Paragraph(strategy_notes, normal_style))

                        content.append(Spacer(1, 0.5 * inch))

                # Defensive Analysis
                defensive_analysis = team_analysis.get('defensive_analysis', {})
                if defensive_analysis:
                    content.append(Paragraph("Defensive Analysis", heading_style))
                    content.append(Spacer(1, 0.25 * inch))

                    # Defense type and characteristics
                    defense_type = defensive_analysis.get('defense_type', 'Unknown')
                    defense_subtype = defensive_analysis.get('defense_subtype')
                    defense_desc = f"{defense_type}"
                    if defense_subtype:
                        defense_desc += f" ({defense_subtype})"

                    content.append(Paragraph(f"Defense Type: {defense_desc}", subheading_style))
                    content.append(Paragraph(f"Pressure Level: {defensive_analysis.get('pressure_level', 'Unknown')}", normal_style))
                    content.append(Paragraph(f"Pick Up Point: {defensive_analysis.get('pick_up_point', 'Unknown')}", normal_style))
                    content.append(Spacer(1, 0.15 * inch))

                    # Defensive tendencies
                    content.append(Paragraph("Defensive Tendencies:", subheading_style))
                    tendencies = [
                        f"Deny First Pass: {defensive_analysis.get('deny_first_pass', 'Unknown')}",
                        f"Deny Ball Reversal: {defensive_analysis.get('deny_ball_reversal', 'Unknown')}",
                        f"Allow Dribble Penetration: {defensive_analysis.get('allow_dribble_penetration', 'Unknown')}"
                    ]
                    for tendency in tendencies:
                        content.append(Paragraph(f"• {tendency}", normal_style))
                    content.append(Spacer(1, 0.15 * inch))

                    # Key defensive personnel
                    content.append(Paragraph("Key Defensive Personnel:", subheading_style))
                    if defensive_analysis.get('best_on_ball_defenders'):
                        content.append(Paragraph(f"Best On-Ball Defenders: {', '.join(defensive_analysis.get('best_on_ball_defenders', []))}", normal_style))
                    if defensive_analysis.get('weak_on_ball_defenders'):
                        content.append(Paragraph(f"Weak On-Ball Defenders: {', '.join(defensive_analysis.get('weak_on_ball_defenders', []))}", normal_style))
                    content.append(Spacer(1, 0.15 * inch))

                    # Notes
                    if defensive_analysis.get('notes'):
                        content.append(Paragraph("Notes:", subheading_style))
                        content.append(Paragraph(defensive_analysis.get('notes', ''), normal_style))
                        content.append(Spacer(1, 0.25 * inch))

                # Shot Chart Analysis
                shot_chart = analysis_results.get('shot_chart', {})
                if shot_chart:
                    content.append(Paragraph("Shot Distribution Analysis", heading_style))
                    content.append(Spacer(1, 0.25 * inch))

                    # Zone statistics
                    zone_stats = shot_chart.get('zone_stats', {})
                    if zone_stats:
                        content.append(Paragraph("Shooting by Zone:", subheading_style))

                        # Create table for zone stats
                        zone_data = [["Zone", "Attempts", "Made", "Percentage"]]
                        for zone, stats in zone_stats.items():
                            zone_data.append([
                                zone,
                                str(stats.get('attempts', 0)),
                                str(stats.get('made', 0)),
                                f"{stats.get('percentage', 0)}%"
                            ])

                        zone_table = Table(zone_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
                        zone_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        content.append(zone_table)
                        content.append(Spacer(1, 0.25 * inch))

                # Play Type Analysis
                play_type_analysis = analysis_results.get('play_type_analysis', {})
                if play_type_analysis:
                    content.append(Paragraph("Play Type Analysis", heading_style))
                    content.append(Spacer(1, 0.25 * inch))

                    # Play type data
                    play_data = play_type_analysis.get('play_data', {})
                    if play_data:
                        content.append(Paragraph("Play Type Breakdown:", subheading_style))

                        # Create table for play type stats
                        play_type_data = [["Play Type", "Frequency", "PPP", "FG%", "Strength"]]
                        for play_type, stats in play_data.items():
                            play_type_data.append([
                                play_type,
                                f"{stats.get('percentage', 0)}%",
                                str(stats.get('points_per_possession', 0)),
                                f"{stats.get('field_goal_percentage', 0)}%",
                                "Yes" if stats.get('is_strength', False) else "No"
                            ])

                        play_type_table = Table(play_type_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
                        play_type_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        content.append(play_type_table)
                        content.append(Spacer(1, 0.15 * inch))

                    # Recommendations
                    recommendations = play_type_analysis.get('recommendations', [])
                    if recommendations:
                        content.append(Paragraph("Recommendations:", subheading_style))
                        for rec in recommendations:
                            content.append(Paragraph(f"• {rec}", normal_style))
                        content.append(Spacer(1, 0.25 * inch))

                # Advanced Metrics
                advanced_metrics = analysis_results.get('advanced_metrics', {})
                if advanced_metrics:
                    content.append(Paragraph("Advanced Team Metrics", heading_style))
                    content.append(Spacer(1, 0.25 * inch))

                    # Team metrics
                    team_metrics = advanced_metrics.get('team_metrics', {})
                    if team_metrics:
                        # Create table for team metrics
                        metrics_data = [
                            ["Metric", "Value"],
                            ["Offensive Rating", str(team_metrics.get('offensive_rating', 0))],
                            ["Defensive Rating", str(team_metrics.get('defensive_rating', 0))],
                            ["Net Rating", str(team_metrics.get('net_rating', 0))],
                            ["Pace", str(team_metrics.get('pace', 0))],
                            ["True Shooting %", f"{team_metrics.get('true_shooting', 0)}%"],
                            ["Effective FG %", f"{team_metrics.get('effective_fg', 0)}%"],
                            ["Turnover Rate", f"{team_metrics.get('turnover_rate', 0)}%"],
                            ["Assist Rate", f"{team_metrics.get('assist_rate', 0)}%"]
                        ]

                        metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch])
                        metrics_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        content.append(metrics_table)
                        content.append(Spacer(1, 0.25 * inch))

            # Build the PDF
            doc.build(content)
            logger.info(f"PDF generated at: {pdf_path}")

            return pdf_path
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}", exc_info=True)

            # Create a simple fallback PDF if the fancy one fails
            fallback_pdf_path = os.path.join(reports_dir, f"fallback_{pdf_filename}")

            try:
                with open(fallback_pdf_path, "w") as f:
                    f.write(f"Scouting Report: {report.title}\n\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
                    f.write(f"Team: {report.team_name or 'N/A'}\n")
                    f.write(f"Opponent: {report.opponent_name or 'N/A'}\n\n")

                    # Add some basic analysis info
                    team_analysis = analysis_results.get('team_analysis', {})
                    if team_analysis:
                        f.write("Team Analysis:\n")
                        f.write(f"Team: {team_analysis.get('team_name', 'Unknown')}\n\n")

                        # Add player info with jersey numbers
                        players = team_analysis.get('players', [])
                        if players:
                            f.write("Player Analysis:\n")
                            for player in players:
                                jersey_number = player.get('jersey_number', 'N/A')
                                player_name = player.get('name', f"Player #{jersey_number}")
                                position = player.get('position', 'Unknown')
                                f.write(f"#{jersey_number} - {player_name} ({position})\n")
                            f.write("\n")

                        # Add defensive analysis
                        defensive_analysis = team_analysis.get('defensive_analysis', {})
                        if defensive_analysis:
                            f.write("Defensive Analysis:\n")
                            defense_type = defensive_analysis.get('defense_type', 'Unknown')
                            defense_subtype = defensive_analysis.get('defense_subtype')
                            defense_desc = f"{defense_type}"
                            if defense_subtype:
                                defense_desc += f" ({defense_subtype})"
                            f.write(f"Defense Type: {defense_desc}\n")
                            f.write(f"Pressure Level: {defensive_analysis.get('pressure_level', 'Unknown')}\n")
                            f.write(f"Notes: {defensive_analysis.get('notes', '')}\n\n")

                    # Add shot chart summary
                    shot_chart = analysis_results.get('shot_chart', {})
                    if shot_chart:
                        f.write("Shot Distribution Analysis:\n")
                        zone_stats = shot_chart.get('zone_stats', {})
                        for zone, stats in zone_stats.items():
                            f.write(f"{zone}: {stats.get('made', 0)}/{stats.get('attempts', 0)} ({stats.get('percentage', 0)}%)\n")
                        f.write("\n")

                    # Add play type analysis summary
                    play_type_analysis = analysis_results.get('play_type_analysis', {})
                    if play_type_analysis:
                        f.write("Play Type Analysis:\n")
                        strengths = play_type_analysis.get('strengths', [])
                        if strengths:
                            f.write("Strengths: " + ", ".join(strengths) + "\n")
                        weaknesses = play_type_analysis.get('weaknesses', [])
                        if weaknesses:
                            f.write("Weaknesses: " + ", ".join(weaknesses) + "\n")
                        f.write("\n")

                logger.info(f"Fallback PDF generated at: {fallback_pdf_path}")
                return fallback_pdf_path
            except Exception as fallback_error:
                logger.error(f"Error generating fallback PDF: {str(fallback_error)}", exc_info=True)

                # Last resort: create an empty file
                empty_pdf_path = os.path.join(reports_dir, f"empty_{pdf_filename}")
                with open(empty_pdf_path, "w") as f:
                    f.write("Error generating scouting report. Please try again.")

                return empty_pdf_path


# Create a singleton instance
pdf_generator_service = PDFGeneratorService()
