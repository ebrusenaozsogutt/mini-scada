## Demo Preview

### Main Screen
![Main Screen](main-screen.png)

### Animated Demo
![Demo GIF](demo.gif)

### Additional Screen
![Monitoring Screen](second-screen.png)

### Additional Screen
![Monitoring Screen](third-screen.png)

---

# Mini SCADA-Inspired Industry 4.0 Desktop Application

This project is a desktop application developed as part of my internship work.

It was designed within the context of **Industry 4.0** as a **mini SCADA-inspired software system** for monitoring, analyzing, and reporting machine temperature data in real time. The application simulates an industrial machine environment by generating both **normal and abnormal temperature values** through a temperature simulator developed in **C#**.

The generated simulation data is stored in a **SQLite database**, and then processed, analyzed, visualized, and tabulated using Python-based data analysis libraries such as **Scikit-learn**, **Pandas**, **NumPy**, and **Matplotlib**. The processed outputs are transferred to the desktop application and presented through real-time graphical panels and monitoring modules.

The system is designed not only as a temperature monitoring tool, but also as a scalable foundation for a more advanced industrial digital monitoring platform.

---

## Project Overview

The project follows a mini SCADA logic and aims to simulate an industrial machine health monitoring system.

A temperature simulator generates industrially relevant machine temperature values, including both normal and abnormal conditions. These values are stored in a database structure created with SQLite. The stored data is later retrieved and processed using Python tools for analysis, visualization, and reporting purposes.

The desktop application presents this information simultaneously through:
- real-time temperature displays,
- graphical monitoring panels,
- abnormal value indicators,
- and process timeline views.

This structure enables the user to observe temperature behavior, detect abnormal conditions, and evaluate how long abnormal values persist over time.

---

## Main Features

- Mini SCADA-inspired desktop monitoring interface
- Industry 4.0-oriented system design
- Real-time temperature simulation in C#
- Simulation of both normal and abnormal machine temperature values
- SQLite-based database storage
- Data processing and analysis using Python
- Visualization and tabulation with Pandas, NumPy, Scikit-learn, and Matplotlib
- Simultaneous transfer of processed data to the desktop interface
- Real-time graphical display modules
- Abnormal temperature detection and display
- Process timeline tracking
- Duration-based abnormal condition analysis
- Reporting system integrated into the application
- Excel export feature via **Download Reports** button

---

## System Architecture

The system is structured as a multi-stage industrial data workflow:

1. **Temperature Simulation Layer**  
   A machine-oriented temperature simulation is developed in C# to generate both normal and abnormal temperature values.

2. **Database Layer**  
   The generated values are stored in a SQLite database.

3. **Data Analysis Layer**  
   The stored data is retrieved and analyzed using Python libraries such as:
   - Scikit-learn
   - Pandas
   - NumPy
   - Matplotlib

4. **Visualization and Reporting Layer**  
   The analyzed data is visualized, tabulated, and prepared for reporting.

5. **Desktop Monitoring Interface**  
   The outputs are transferred to the desktop application and displayed through real-time monitoring panels, abnormal value indicators, charts, and process timelines.

---

## Technologies Used

### Desktop Application
- C#
- Desktop application development
- Real-time monitoring logic

### Database
- SQLite

### Data Analysis & Visualization
- Python
- Scikit-learn
- Pandas
- NumPy
- Matplotlib

### Reporting
- Excel export / report generation

---

## How the System Works

The project starts with a temperature simulator that produces machine temperature data suitable for an industrial scenario. These values may represent both stable operating conditions and abnormal operating conditions.

The generated data is written into a SQLite database. Afterward, the stored records are retrieved and processed with Python-based analysis tools. During this stage, the data is:
- cleaned and organized,
- analyzed,
- visualized through charts,
- and transformed into structured tables and reports.

These processed outputs are then transferred to the desktop application, where they are shown in real time using graphical monitoring modules.

The application also identifies abnormal values and shows them directly on the interface. In addition, it includes a **process timeline**, allowing the user to determine:
- how many abnormal values occurred,
- how long abnormal conditions lasted,
- and how the temperature behavior changed over time.

---

## Monitoring and Analysis Capabilities

The application provides a simplified but practical industrial monitoring experience by combining simulation, database management, analysis, and interface visualization.

It enables users to:
- track live temperature values,
- observe abnormal conditions,
- review process-based graphical outputs,
- evaluate abnormal duration periods,
- and generate downloadable reports.

This makes the project more than a simple simulation tool; it becomes a prototype for a scalable smart monitoring system.

---

## Reporting System

The application includes a reporting module.

Users can download generated reports in **Excel format** through the **Download Reports** button integrated into the desktop interface. This allows temperature data, analysis results, and abnormal condition records to be exported for further review, documentation, or presentation.

---

## Abnormal Value Tracking

One of the important parts of the project is the handling of abnormal temperature values.

The system can indicate:
- when abnormal temperature values occur,
- how frequently they occur,
- and how long they continue during a given process.

This supports a basic predictive and analytical monitoring approach, especially for industrial process observation and machine condition awareness.

---

## Future Development Potential

The project was designed with future scalability in mind.

In its next stages, the system can be extended by integrating additional industrial parameters such as:
- current
- pressure
- operating time
- and other machine-related variables

It can also be improved with:
- alarm system integration
- Telegram bot notifications
- email-based warning systems
- AI-supported analysis
- digital twin logic
- machine health prediction modules
- intelligent suggestions for future maintenance or machine issues

With artificial intelligence integration, the software can evolve into a more complete **digital twin-inspired monitoring platform**, capable of evaluating machine health and offering predictive recommendations about possible future problems.

---

## Industry 4.0 Perspective

This project was designed not only as a software development exercise, but also as a conceptual step toward Industry 4.0 applications.

It combines:
- simulation,
- database systems,
- desktop software,
- data analysis,
- reporting,
- visualization,
- and future AI integration potential

into a single monitoring-oriented architecture.

In this sense, the project reflects the logic of smart manufacturing systems and digital transformation in industrial environments.

---


## Screenshots

| Main Interface | Monitoring View |
|----------------|-----------------|
| ![](images/main-screen.png) | ![](images/second-screen.png) |

---

## Technical Details

<details>
<summary>Click to expand technical summary</summary>

- Mini SCADA-inspired monitoring architecture
- Industry 4.0 concept-based design
- C# temperature simulator for industrial machine conditions
- Normal and abnormal temperature data generation
- SQLite-based data storage
- Python-based analysis and visualization workflow
- Real-time graphical transfer to desktop interface
- Abnormal condition duration tracking
- Excel reporting support
- Scalable structure for future AI and digital twin integration

</details>

---

## Internship Project Note

This project was developed during my internship period.

It represents a combination of industrial automation logic, desktop software development, data analysis, and reporting systems. Beyond temperature monitoring, it was also designed as a scalable prototype that can be expanded into a broader machine monitoring and digital twin platform in the future.

---

## Author

Developed by **Hilal Yeşim Altunay**

Internship Project – Mini SCADA-Inspired Industry 4.0 Desktop Monitoring and Analysis System

## How to Run

1. Clone the repository:
```bash
