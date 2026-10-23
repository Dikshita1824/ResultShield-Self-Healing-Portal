package com.resultshield.resultshield;

import java.util.List;

import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class DataSeeder {

    @Bean
    CommandLineRunner seedStudents(StudentRepository studentRepository) {

        return args -> {

            // Existing records ko duplicate nahi karna
            if (studentRepository.count() > 0) {
                System.out.println(
                    "ResultShield: Existing student records found. Skipping demo data."
                );
                return;
            }

            List<Student> students = List.of(
                new Student("101", "Aarav Sharma", 85),
                new Student("102", "Priya Verma", 92),
                new Student("103", "Rohan Singh", 67),
                new Student("104", "Ananya Gupta", 78),
                new Student("105", "Kabir Mehta", 56),
                new Student("106", "Diya Joshi", 95),
                new Student("107", "Arjun Patel", 72),
                new Student("108", "Meera Jain", 88),
                new Student("109", "Vivaan Kapoor", 61),
                new Student("110", "Ishita Rao", 81),
                new Student("111", "Aditya Khan", 74),
                new Student("112", "Sana Ali", 90),
                new Student("113", "Reyansh Das", 69),
                new Student("114", "Kavya Nair", 84),
                new Student("115", "Dev Malhotra", 58),
                new Student("116", "Tara Mishra", 97),
                new Student("117", "Neil Sethi", 76),
                new Student("118", "Aditi Saxena", 63),
                new Student("119", "Yash Bansal", 89),
                new Student("120", "Myra Kapoor", 93)
            );

            studentRepository.saveAll(students);

            System.out.println(
                "ResultShield: Automatically inserted "
                + students.size()
                + " demo student records."
            );
        };
    }
}