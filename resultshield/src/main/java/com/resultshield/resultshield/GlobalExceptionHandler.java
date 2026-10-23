package com.resultshield.resultshield;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.server.ResponseStatusException;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<String> handleNotFound(
            ResponseStatusException exception) {

        return ResponseEntity
                .status(HttpStatus.NOT_FOUND)
                .body("No result found. Please check the roll number.");
    }
}