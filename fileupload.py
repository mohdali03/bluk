        
from flask import  flash, jsonify, redirect, url_for 

from models import db, Student
import csv
import io
import openpyxl


def csvUpload(file):
    try:
        data = file.read()  
        stream = io.StringIO(data.decode("UTF-8"))  
        reader = csv.reader(stream)
        header = next(reader, None)
        if header is None:
            return jsonify({"error": "Empty or invalid CSV file"}), 400
        
        existing_rollnos = {student.rollNo for student in Student.query.with_entities(Student.rollNo).all()}

        count = 0
        duplicates = 0
        for row in reader:
            if row[1] in existing_rollnos:
                duplicates +=1
                continue 
                
            newStudent = Student(*row)
            db.session.add(newStudent)

            count +=1
        db.session.commit()
        
        flash(f"Successfully added {count} students! Skipped {duplicates} duplicates.", "success")
        return redirect(url_for('home'))
    except Exception as e:
        return jsonify({"error": f"Failed to process the file: {str(e)}"}), 500
        
def excelUpload(file):
    try:
        workbook = openpyxl.load_workbook(file)
        sheet = workbook.active
        
        
        existing_rollnos = {student.rollNo for student in Student.query.with_entities(Student.rollNo).all()}

        
        count = 0
        duplicates = 0
        for row in sheet.iter_rows(min_row=2, values_only=True): # type:ignore
            count +=1
            if row[1] in existing_rollnos:
                duplicates +=1
                continue 
                
            newStudent = Student(*row)
            db.session.add(newStudent)
            existing_rollnos.add(row[1])
        db.session.commit()
        flash(f"Successfully added {count} students! Skipped {duplicates} duplicates.", "success")
        return redirect(url_for('home'))
    except Exception as e:
            return jsonify({"error": f"Failed to process the file: {str(e)}"}), 500
