import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

public class TriggerCodUserSearch {

    public static class User {
        private final int id;
        private final String username;
        private final String role;

        public User(int id, String username, String role) {
            this.id = id;
            this.username = username;
            this.role = role;
        }

        @Override
        public String toString() {
            return "User{id=" + id + ", username='" + username + "', role='" + role + "'}";
        }
    }

    public static class UserRepository {
        private final String connectionUrl = "jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1";

        public UserRepository() {
            try (Connection conn = DriverManager.getConnection(connectionUrl);
                 Statement stmt = conn.createStatement()) {
                stmt.execute("CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, username VARCHAR(255), role VARCHAR(255))");
                stmt.execute("INSERT INTO users VALUES (1, 'alice', 'ADMIN')");
                stmt.execute("INSERT INTO users VALUES (2, 'bob', 'USER')");
                stmt.execute("INSERT INTO users VALUES (3, 'charlie', 'USER')");
            } catch (SQLException e) {
                throw new RuntimeException(e);
            }
        }

        public List<User> getUserByNameVulnerable(String name) {
            List<User> users = new ArrayList<>();
            String query = "SELECT id, username, role FROM users WHERE username = '" + name + "'";
            try (Connection conn = DriverManager.getConnection(connectionUrl);
                 Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery(query)) {
                while (rs.next()) {
                    users.add(new User(rs.getInt("id"), rs.getString("username"), rs.getString("role")));
                }
            } catch (SQLException e) {
                System.err.println("Database error: " + e.getMessage());
            }
            return users;
        }

        public List<User> getUserByNameSecure(String name) {
            List<User> users = new ArrayList<>();
            String query = "SELECT id, username, role FROM users WHERE username = ?";
            try (Connection conn = DriverManager.getConnection(connectionUrl);
                 PreparedStatement pstmt = conn.getPreparedStatement(query)) {
                pstmt.setString(1, name);
                try (ResultSet rs = pstmt.executeQuery()) {
                    while (rs.next()) {
                        users.add(new User(rs.getInt("id"), rs.getString("username"), rs.getString("role")));
                    }
                }
            } catch (SQLException e) {
                System.err.println("Database error: " + e.getMessage());
            }
            return users;
        }
    }

    public static void main(String[] args) {
        UserRepository repository = new UserRepository();

        System.out.println("--- Vulnerable Method: Safe Input ---");
        List<User> safeResult = repository.getUserByNameVulnerable("bob");
        safeResult.forEach(System.out.println);

        System.out.println("\n--- Vulnerable Method: Malicious SQL Injection Input ---");
        List<User> sqlInjectionResult = repository.getUserByNameVulnerable("malicious' OR '1'='1");
        sqlInjectionResult.forEach(System.out.println);

        System.out.println("\n--- Secure Method: Safe Input ---");
        List<User> secureSafeResult = repository.getUserByNameSecure("bob");
        secureSafeResult.forEach(System.out.println);

        System.out.println("\n--- Secure Method: Malicious Input Defended ---");
        List<User> secureBlockedResult = repository.getUserByNameSecure("malicious' OR '1'='1");
        secureBlockedResult.forEach(System.out.println);
    }
}
