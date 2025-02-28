
import java.sql.*;

public class RegisterDao {
	
	//private String dbUrl = "jdbc:mysql://localhost:3306/userdb";
	//private String dbUname = "root";
	//private String dbPassword = "rootpasswordgiven";
	// String dbDriver = "com.mysql.cj.jdbc.Driver";
	
	
	  private String dbUrl = "jdbc:postgresql://10.170.1.24:5432/userdb"; private
	  String dbUname = "postgres"; private String dbPassword = "awxpass"; private
	  String dbDriver = "org.postgresql.Driver";
	 
    
	/*
	 * private String dbUrl = "jdbc:oracle:thin:@192.168.1.231:1521:STDEMO"; private
	 * String dbUname = "demo"; private String dbPassword = "demo"; private String
	 * dbDriver = "oracle.jdbc.driver.OracleDriver";
	 */
	
	public void loadDriver(String dbDriver)
	{
		try {
			Class.forName(dbDriver);
		} catch (ClassNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	public Connection getConnection()
	{
		Connection con = null;
		try {
			con = DriverManager.getConnection(dbUrl, dbUname, dbPassword);
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return con;
	}
	
	
	public String insert(Member member)
	{
		loadDriver(dbDriver);
		Connection con = getConnection();
		String result = "Data entered successfully";
		String sql = "insert into member values(?,?,?,?)";
		
		PreparedStatement ps;
		try {
		ps = con.prepareStatement(sql);
		ps.setString(1, member.getUname());
		ps.setString(2, member.getPassword());
		ps.setString(3, member.getEmail());
		ps.setString(4, member.getPhone());
		ps.executeUpdate();
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			result = "Data not entered";
		}
		return result;
	}

}
