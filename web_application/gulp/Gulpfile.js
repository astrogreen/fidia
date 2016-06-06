/*!
 * gulp
 * $ npm install gulp-autoprefixer gulp-cssnano gulp-imagemin gulp-rename
 */

// Load plugins

var gulp = require('gulp'),
    autoprefixer = require('gulp-autoprefixer'),
    cssnano = require('gulp-cssnano'),
    imagemin = require('gulp-imagemin'),
    rename = require("gulp-rename"),
    path = require('path'),
    notify = require('gulp-notify');

// Images
// gulp.task('images', function() {
//   return gulp.src('restapi_app/static/restapi_app/img/**/*')
//     .pipe(imagemin({ optimizationLevel: 3, progressive: true, interlaced: true }))
//     .pipe(gulp.dest('dist/assets/img'))
//     .pipe(notify({ message: 'Images task complete' }));
// });

// Styles
// gulp.task('styles', function() {
//     // minify less/ css files and copy to css/filename/filename.min.css
//   return gulp.src('restapi_app/static/restapi_app/less/main.css')
//     .pipe(autoprefixer('last 2 version'))
//     .pipe(rename(function(file){
//         // join the base name (e.g., main) to the file path, effectively forcing gulp to create the folder if it doesn't
//         // exist already
//         file.dirname = path.join(file.dirname, file.basename)
//     }))
//     .pipe(rename({suffix: '.min'}))
//     .pipe(cssnano())
//     .pipe(gulp.dest('restapi_app/static/restapi_app/css/'))
//     // .pipe(notify({ message: 'Styles task complete' }));
// });


// Default task
gulp.task('default', function(){
    gulp.start('styles'); 
});

// Watch
gulp.task('watch', function(){
    // watch the css files in the less directory (transpiler will update if less is altered)
    // minify and move to css/folder/
    gulp.watch(['restapi_app/static/restapi_app/less/*.css', 'restapi_app/static/restapi_app/less/**/*.css'], function(file){
    })
        .on("change", function(file){
            return gulp.src(file.path)
                .pipe(autoprefixer('last 2 version'))
                .pipe(rename(function(file){
                    // join the base name (e.g., main) to the file path, effectively forcing gulp to create the folder if it doesn't
                    // exist already
                    file.dirname = path.join(file.dirname, file.basename)
                }))
                .pipe(rename({suffix: '.min'}))
                .pipe(cssnano())
                .pipe(gulp.dest('restapi_app/static/restapi_app/css/'))
                .pipe(notify({ message: 'Styles task complete' }));
        })
});