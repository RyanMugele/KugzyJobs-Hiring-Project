# Content Creator Platform - Database Relationships and Field Explanations

## Core User Management

### User Table (Central Hub)
**Purpose**: Stores common information for all platform users regardless of their role.

**Key Fields Explained**:
- `userId`: Unique identifier for each user (primary key)
- `userType`: Determines if user is 'creator', 'editor', or 'admin'
- `averageRating`: Calculated field storing user's overall rating (updated when new ratings are received)
- `totalRatings`: Count of ratings received (helps determine rating reliability)
- `profilePicture`: URL/path to user's profile image
- `passwordHash`: Encrypted password for security
- `dateCreated/lastUpdated`: Audit trail for when records are created/modified

**Relationship**: One user can have only one role, but the platform can have many users of each type.

### Creator Table
**Relationship**: One user can be one creator, and one creator belongs to one user (1:1 relationship implemented as separate table for clean separation of concerns).

**Key Fields Explained**:
- `userId`: Links to the main user record (foreign key)
- `contentType`: What type of content they create (e.g., "YouTube videos", "Instagram reels")
- `platformFocus`: Which platform they focus on (e.g., "YouTube", "TikTok", "Instagram")

**Why Separate Table**: Keeps creator-specific data organized and allows for easy extension of creator features without affecting other user types.

### Editor Table
**Relationship**: One user can be one editor, and one editor belongs to one user (1:1 relationship).

**Key Fields Explained**:
- `specializations`: Text field listing editor's skills (e.g., "Video editing, Color grading, Motion graphics")
- `experienceLevel`: Editor's skill level for filtering purposes
- `hourlyRate`: Editor's proposed hourly rate for budgeting
- `isVerified`: Boolean indicating if admin has approved this editor's portfolio
- `verificationStatus`: Current verification state in the approval workflow

**Why Separate Table**: Editor-specific fields that don't apply to creators or admins.

### Admin Table
**Relationship**: One user can be one admin, and one admin belongs to one user (1:1 relationship).

**Key Fields Explained**:
- `roleDesignation`: Admin's specific role (e.g., "Super Admin", "Content Moderator")

---

## Portfolio Management

### Portfolio Table
**Relationship**: One editor can have many portfolio items, but each portfolio item belongs to one editor (1:Many relationship).

**Key Fields Explained**:
- `editorId`: Links portfolio item to specific editor
- `title`: Name of the portfolio piece
- `description`: Details about the work
- `videoUrl`: Link to the actual video file
- `skillTags`: Simple text field listing relevant skills demonstrated
- `verificationStatus`: Whether admin has approved this portfolio item
- `rejectionReason`: If rejected, why it was rejected

**Business Logic**: Editors build portfolios to showcase their work. Admins verify quality before creators can see them. This ensures platform quality control.

---

## Job Management System

### Job Table
**Relationship**: One creator can post many jobs, but each job belongs to one creator (1:Many relationship).

**Key Fields Explained**:
- `creatorId`: Links job to the creator who posted it
- `title`: Job name/title
- `description`: Detailed job requirements
- `budgetMin/budgetMax`: Budget range for the project
- `deadline`: When the work needs to be completed
- `requiredSkills`: Text field listing needed skills
- `status`: Current job state (posted → in_progress → completed)
- `selectedEditorId`: Which editor was chosen (NULL until decision made)
- `deliverableUrl`: Link to final work when completed

**Business Logic**: Creators post jobs → Editors apply → Creator selects editor → Work progresses → Job completed.

### Job Application Table (Conjunction Table)
**Relationship**: One editor can apply to many jobs, and one job can receive many applications from different editors (Many:Many relationship handled through conjunction table).

**Key Fields Explained**:
- `jobId`: Links to the specific job
- `editorId`: Links to the applying editor
- `proposedRate`: Editor's bid for this specific job
- `proposedTimeline`: How long editor thinks job will take
- `customProposal`: Editor's personalized pitch
- `status`: Application state (pending → accepted/declined)

**Why Conjunction Table**: Handles the complex many-to-many relationship between jobs and editors. One editor can apply to multiple jobs, and one job receives multiple applications.

---

## Payment System

### Payment Table
**Relationship**: One job can have one payment agreement, and each payment belongs to one job (1:1 relationship).

**Key Fields Explained**:
- `jobId`: Links payment to specific job
- `agreedAmount`: Final agreed payment amount
- `status`: Payment progress (agreed → paid → completed)
- `paymentMethod`: How payment was made
- `mpesaReference`: M-Pesa transaction reference if applicable
- `invoiceNumber`: Generated invoice reference

### Payment Interim Table (Critical for Pesapal Integration)
**Relationship**: One payment can have one interim record, and each interim record belongs to one payment (1:1 relationship).

**Key Fields Explained**:
- `paymentId`: Links to main payment record
- `orderTrackingId`: Pesapal's tracking identifier
- `merchantReference`: Unique reference for this transaction
- `iframeSrc`: Pesapal payment page URL
- `status`: Payment processing state (SAVED → COMPLETED/FAILED)

**Why This Table**: Essential for Pesapal payment gateway integration. Stores temporary payment data during processing, allowing system to track payments through Pesapal's workflow and handle callbacks properly.

---

## Rating and Feedback System

### Rating Table (Conjunction Table)
**Relationship**: After each completed job, both the creator and editor can rate each other. One user can give many ratings to different users, and one user can receive many ratings (Many:Many relationship).

**Key Fields Explained**:
- `jobId`: Links rating to specific completed project
- `raterId`: User giving the rating
- `rateeId`: User receiving the rating
- `ratingValue`: 1-5 star rating
- `reviewText`: Optional written feedback

**Why Conjunction Table**: Handles the complex relationship where users rate each other. Prevents duplicate ratings for the same job and maintains accountability.

**Business Logic**: Ratings update the `averageRating` and `totalRatings` fields in the User table for display purposes.

---

## Communication System

### Message Table
**Relationship**: One user can send many messages, and one user can receive many messages (1:Many relationships from both sender and receiver perspectives).

**Key Fields Explained**:
- `jobId`: Optional link to related job (can be NULL for general messages)
- `senderId`: User sending the message
- `receiverId`: User receiving the message
- `subject`: Message subject line
- `messageContent`: The actual message text

**Business Logic**: Supports email-based communication with message logging for reference. Not real-time chat, but communication tracking.

---

## Content Moderation

### Report Table
**Relationship**: One user can make many reports, and users/content can receive many reports (1:Many relationships).

**Key Fields Explained**:
- `reporterId`: User making the report
- `reportedUserId`: User being reported (optional)
- `reportedPortfolioId`: Portfolio item being reported (optional)
- `reportReason`: Why the report was made
- `status`: Report processing state
- `adminNotes`: Admin's notes on resolution

**Business Logic**: Allows community moderation where users can report inappropriate content or behavior for admin review.

---

## Security and Authentication

### Password Reset Token Table
**Relationship**: One user can have multiple password reset tokens over time, but each token belongs to one user (1:Many relationship).

**Key Fields Explained**:
- `userId`: User requesting password reset
- `token`: Unique token generated by Werkzeug
- `expiresAt`: When token becomes invalid
- `isUsed`: Whether token has been used already

**Why This Table**: Implements secure password reset using temporary tokens instead of insecure methods.

---

## Database Design Principles Applied

### Star-Shaped Design
- **User table at center**: All major entities connect back to users
- **Minimal mesh relationships**: Avoids complex interconnections
- **Clean separation**: Each table has a clear, single purpose

### Conjunction Tables Used
1. **Job Application**: Handles editor-job applications (many-to-many)
2. **Rating**: Handles user-to-user ratings (many-to-many)

### Performance Considerations
- **Calculated fields**: `averageRating` and `totalRatings` in User table avoid complex calculations
- **Strategic indexes**: On frequently queried fields like email, verification status, job status
- **Appropriate data types**: DECIMAL for money, ENUM for status fields, TEXT for long content

### Data Integrity
- **Foreign key constraints**: Ensure referential integrity
- **Unique constraints**: Prevent duplicate applications, ratings
- **Check constraints**: Ensure ratings are 1-5 stars
- **Default values**: Provide sensible defaults for optional fields
