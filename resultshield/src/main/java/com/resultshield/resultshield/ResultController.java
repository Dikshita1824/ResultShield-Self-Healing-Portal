package com.resultshield.resultshield;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
public class ResultController {

    private final StudentRepository studentRepository;

    public ResultController(StudentRepository studentRepository) {
        this.studentRepository = studentRepository;
    }

    @GetMapping("/result")
    public Student getResult(@RequestParam String rollNumber) {

        return studentRepository.findByRollNumber(rollNumber)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "No result found for Roll Number: " + rollNumber
                ));
    }
}