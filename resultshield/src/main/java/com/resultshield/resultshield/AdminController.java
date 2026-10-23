package com.resultshield.resultshield;

import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/admin/students")
public class AdminController {

    private final StudentRepository studentRepository;

    public AdminController(StudentRepository studentRepository) {
        this.studentRepository = studentRepository;
    }

    // Add a student
    @PostMapping
    public Student addStudent(@RequestBody Student student) {

        if (student.getRollNumber() == null ||
            student.getRollNumber().isBlank() ||
            student.getName() == null ||
            student.getName().isBlank() ||
            student.getMarks() < 0 ||
            student.getMarks() > 100) {

            throw new ResponseStatusException(
                HttpStatus.BAD_REQUEST,
                "Enter valid roll number, name and marks between 0 and 100"
            );
        }

        if (studentRepository.existsById(student.getRollNumber())) {
            throw new ResponseStatusException(
                HttpStatus.CONFLICT,
                "Student roll number already exists"
            );
        }

        return studentRepository.save(student);
    }

    // Get all students
    @GetMapping
    public List<Student> getAllStudents() {
        return studentRepository.findAll();
    }

    // Get one student
    @GetMapping("/{rollNumber}")
    public Student getStudent(@PathVariable String rollNumber) {
        return studentRepository.findByRollNumber(rollNumber)
            .orElseThrow(() -> new ResponseStatusException(
                HttpStatus.NOT_FOUND,
                "Student not found"
            ));
    }

    // Update student
    @PutMapping("/{rollNumber}")
    public Student updateStudent(
            @PathVariable String rollNumber,
            @RequestBody Student updatedStudent) {

        Student existingStudent = studentRepository
            .findByRollNumber(rollNumber)
            .orElseThrow(() -> new ResponseStatusException(
                HttpStatus.NOT_FOUND,
                "Student not found"
            ));

        if (updatedStudent.getName() == null ||
            updatedStudent.getName().isBlank() ||
            updatedStudent.getMarks() < 0 ||
            updatedStudent.getMarks() > 100) {

            throw new ResponseStatusException(
                HttpStatus.BAD_REQUEST,
                "Enter a valid name and marks between 0 and 100"
            );
        }

        existingStudent.setName(updatedStudent.getName());
        existingStudent.setMarks(updatedStudent.getMarks());

        return studentRepository.save(existingStudent);
    }

    // Delete student
    @DeleteMapping("/{rollNumber}")
    public String deleteStudent(@PathVariable String rollNumber) {

        Student student = studentRepository
            .findByRollNumber(rollNumber)
            .orElseThrow(() -> new ResponseStatusException(
                HttpStatus.NOT_FOUND,
                "Student not found"
            ));

        studentRepository.delete(student);

        return "Student deleted successfully";
    }
}